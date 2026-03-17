package com.bank.servicepayment.resource;

import com.bank.servicepayment.client.ServiceConnectorClient;
import com.bank.servicepayment.client.ServiceConnectorClient.*;
import com.bank.servicepayment.dto.DebtInfo;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import io.smallrye.common.annotation.Blocking;
import jakarta.inject.Inject;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import java.time.LocalDate;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.eclipse.microprofile.rest.client.inject.RestClient;
import org.jboss.logging.Logger;
import org.jboss.logging.MDC;

@Path("/debts")
@Blocking
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class DebtResource {

    private static final Logger LOG = Logger.getLogger(DebtResource.class);

    @Inject
    ServiceConnectorClient serviceConnectorClient;

    @Inject
    com.bank.servicepayment.service.AuditService auditService;

    @Inject
    MeterRegistry registry;

    @GET
    public Response debtsGet(@QueryParam("service_id") String serviceId,
            @QueryParam("customer_reference") String customerReference) {

        long start = System.nanoTime();
        String status = "SUCCESS";

        MDC.put("service_id", serviceId != null ? serviceId : "unknown");
        MDC.put("customer_reference", customerReference != null ? customerReference : "unknown");
        LOG.infof("Processing debt inquiry for reference: %s", customerReference);

        ProviderDebtRequest request = new ProviderDebtRequest();
        request.service_id = serviceId;
        request.reference = customerReference;

        try {
            ProviderDebtResponse providerResponse = serviceConnectorClient.getDebt(request);

            DebtInfo info = new DebtInfo();
            info.setServiceId(serviceId);
            info.setCustomerReference(customerReference);
            info.setAmount(providerResponse.amount);
            info.setCurrency(providerResponse.currency);
            info.setDueDate(LocalDate.now().plusDays(5)); // Simplified
            info.setDescription(providerResponse.description);
            info.setTargetAccount(providerResponse.target_account);

            auditService.sendAuditEvent("DEBT_INQUIRY", request, info,
                    Map.of("service_id", serviceId, "reference", customerReference));

            LOG.infof("Debt inquiry successful for reference: %s, amount: %s", customerReference, info.getAmount());

            return Response.ok(info).build();
        } catch (Exception e) {
            status = "ERROR";
            LOG.errorf(e, "Error during debt inquiry: %s", e.getMessage());
            auditService.sendAuditEvent("DEBT_INQUIRY_FAILED", request, e.getMessage(),
                    Map.of("service_id", serviceId, "reference", customerReference));
            return Response.status(Response.Status.BAD_GATEWAY).entity("Provider inquiry failed: " + e.getMessage())
                    .build();
        } finally {
            MDC.remove("service_id");
            MDC.remove("customer_reference");
            Timer.builder("business_inquiry_seconds")
                    .tag("service_id", serviceId != null ? serviceId : "unknown")
                    .tag("status", status)
                    .publishPercentileHistogram()
                    .register(registry)
                    .record(System.nanoTime() - start, TimeUnit.NANOSECONDS);
        }
    }
}
