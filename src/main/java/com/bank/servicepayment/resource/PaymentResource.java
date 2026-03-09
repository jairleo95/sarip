package com.bank.servicepayment.resource;

import com.bank.servicepayment.client.ServiceConnectorClient;
import com.bank.servicepayment.client.ServiceConnectorClient.*;
import com.bank.servicepayment.dto.DebtInfo;
import com.bank.servicepayment.dto.PaymentRequest;
import com.bank.servicepayment.dto.PaymentResponse;
import com.bank.servicepayment.model.Transaction;
import com.bank.servicepayment.repository.TransactionRepository;
import com.bank.servicepayment.service.FinancialService;
import com.bank.servicepayment.service.IdempotencyService;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.smallrye.common.annotation.Blocking;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import org.eclipse.microprofile.rest.client.inject.RestClient;

@Path("/payments")
@Blocking
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class PaymentResource {

    @Inject
    IdempotencyService idempotencyService;

    @Inject
    TransactionRepository transactionRepository;

    @Inject
    FinancialService financialService;

    @Inject
    ServiceConnectorClient serviceConnectorClient;

    @Inject
    ObjectMapper objectMapper;

    @Inject
    @org.eclipse.microprofile.reactive.messaging.Channel("payment-events")
    org.eclipse.microprofile.reactive.messaging.Emitter<com.bank.servicepayment.event.PaymentSucceededEvent> eventEmitter;

    @Inject
    com.bank.servicepayment.service.AuditService auditService;

    @Inject
    MeterRegistry registry;

    @Inject
    org.eclipse.microprofile.config.Config config;

    @POST
    public Response paymentsPost(@HeaderParam("X-Idempotency-Key") UUID xIdempotencyKey,
            PaymentRequest paymentRequest) {
        if (paymentRequest == null) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Missing payment request body").build();
        }
        long start = System.nanoTime();
        String status = "SUCCESS";
        String serviceId = paymentRequest != null ? paymentRequest.getServiceId() : "unknown";

        String idempotencyKey = xIdempotencyKey.toString();
        System.out.println("[PaymentResource] Processing payment: " + xIdempotencyKey);

        // 1. Check Idempotency
        String stored = idempotencyService.getStoredResponse(idempotencyKey);
        if (stored != null) {
            System.out.println("[PaymentResource] Returning stored response for: " + idempotencyKey);
            if ("PROCESSING".equals(stored)) {
                return Response.status(102).build();
            }
            try {
                PaymentResponse cachedResponse = objectMapper.readValue(stored, PaymentResponse.class);
                return Response.ok(cachedResponse).build();
            } catch (Exception e) {
                return Response.serverError().build();
            }
        }

        System.out.println("[PaymentResource] Step 2: Marking as processing");
        // 2. Mark as processing
        idempotencyService.markAsProcessing(idempotencyKey);

        // 3. Create Transaction record (PENDING)
        Transaction tx = new Transaction();
        tx.serviceId = serviceId;
        tx.customerReference = paymentRequest.getCustomerReference();
        tx.amount = paymentRequest.getAmount();
        tx.currency = paymentRequest.getCurrency();
        tx.idempotencyKey = idempotencyKey;
        tx.status = "PENDING";

        System.out.println("[PaymentResource] Step 3: Initializing transaction in DB");
        saveTransactionAtomic(tx);

        try {
            // 4. Financial Integrity: Debit Account & Record Ledger
            System.out.println(
                    "[PaymentResource] Step 4: Executing processDebit for Account: " + paymentRequest.getAccountId());
            financialService.processDebit(
                    paymentRequest.getAccountId(),
                    BigDecimal.valueOf(paymentRequest.getAmount()),
                    tx.id);

            // 5. External Integration (Phase 3): Provider Confirmation
            System.out.println("[PaymentResource] Step 5: Calling Service Connector Confirmation...");

            ProviderPayRequest providerRequest = new ProviderPayRequest();
            providerRequest.service_id = tx.serviceId;
            providerRequest.transaction_id = tx.id.toString();
            providerRequest.amount = paymentRequest.getAmount();
            providerRequest.reference = paymentRequest.getCustomerReference();

            ProviderPayResponse providerResponse = serviceConnectorClient.confirmPayment(providerRequest);
            tx.providerEndorsement = providerResponse.endorsement;
            System.out.println("[PaymentResource] Provider confirmation received: " + tx.providerEndorsement);

            // 6. Finalize Transaction
            tx.status = "COMPLETED";
            tx.receiptNumber = "REC-" + System.currentTimeMillis();
            tx.updatedAt = LocalDateTime.now();

            PaymentResponse response = new PaymentResponse();
            response.setTransactionId(tx.id);
            response.setStatus(PaymentResponse.StatusEnum.valueOf(tx.status));
            response.setReceiptNumber(tx.receiptNumber);
            response.setTimestamp(tx.updatedAt.atZone(java.time.ZoneId.systemDefault()).toOffsetDateTime());
            response.setEndorsement(tx.providerEndorsement);

            // 7. Emit Kafka Event
            eventEmitter.send(new com.bank.servicepayment.event.PaymentSucceededEvent(
                    tx.id, tx.serviceId, tx.customerReference, tx.amount, tx.currency, tx.updatedAt.toString()));

            // 8. Save final result in Idempotency store
            idempotencyService.saveResult(idempotencyKey, objectMapper.writeValueAsString(response));

            System.out.println("[PaymentResource] Finalizing transaction status in DB");
            updateTransactionAtomic(tx);

            auditService.sendAuditEvent("PAYMENT_EXECUTION_SUCCESSFUL", paymentRequest, response,
                    Map.of("transaction_id", tx.id, "idempotency_key", idempotencyKey));

            return Response.status(Response.Status.CREATED).entity(response).build();

        } catch (Exception e) {
            System.err.println("[PaymentResource] Error during payment processing: " + e.getMessage());
            e.printStackTrace();
            tx.status = "FAILED";
            tx.updatedAt = LocalDateTime.now();
            updateTransactionAtomic(tx);

            // Determine specific error status
            if (e instanceof jakarta.ws.rs.WebApplicationException) {
                status = String.valueOf(((jakarta.ws.rs.WebApplicationException) e).getResponse().getStatus());
            } else if (e.getMessage() != null && e.getMessage().contains("Connection refused")) {
                status = "503"; // Service Unavailable
            } else {
                status = "500"; // Generic Internal Error
            }

            auditService.sendAuditEvent("PAYMENT_EXECUTION_FAILED", paymentRequest, e.getMessage(),
                    Map.of("transaction_id", tx.id, "idempotency_key", idempotencyKey));

            return Response.status(Integer.parseInt(status == "ERROR" ? "500" : status))
                    .entity(e.getMessage()).build();
        } finally {
            Timer.builder("business_payment_seconds")
                    .tag("service_id", serviceId)
                    .tag("status", status.equals("SUCCESSFUL") ? "201" : status)
                    .publishPercentileHistogram()
                    .register(registry)
                    .record(System.nanoTime() - start, TimeUnit.NANOSECONDS);
        }
    }

    @Transactional
    void saveTransactionAtomic(Transaction tx) {
        transactionRepository.persist(tx);
    }

    @Transactional
    void updateTransactionAtomic(Transaction tx) {
        transactionRepository.getEntityManager().merge(tx);
    }
}
