package com.bank.providersimulator.resource;

import com.bank.providersimulator.model.ServiceProfile;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;

@Path("/mock-provider")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class SimulationResource {

    public record ProviderDebtRequest(String service_id, String reference) {
    }

    public record ProviderDebtResponse(Double amount, String currency, String target_account, String description) {
    }

    public record ProviderPayRequest(String service_id, String transaction_id, Double amount, String reference) {
    }

    public record ProviderPayResponse(String endorsement, String status) {
    }

    @POST
    @Path("/provider-debt")
    public Response getDebt(ProviderDebtRequest request) {
        applySimulation(request.service_id());

        ServiceProfile profile = ProfileResource.getProfile(request.service_id());

        if (profile.functionalError() == ServiceProfile.FunctionalErrorType.DEBT_ANNULLED) {
            return Response.status(422).entity("{\"error\": \"Debt Already Annulled\"}").build();
        }

        if (profile.functionalError() == ServiceProfile.FunctionalErrorType.USER_NOT_FOUND) {
            return Response.status(404).entity("{\"error\": \"User Not Found in Provider System\"}").build();
        }

        ProviderDebtResponse res = new ProviderDebtResponse(
                150.75, "USD", "CORP-" + request.service_id(), "Monthly Service Fee");
        return Response.ok(res).build();
    }

    @POST
    @Path("/provider-pay")
    public Response confirmPayment(ProviderPayRequest request) {
        applySimulation(request.service_id());

        ServiceProfile profile = ProfileResource.getProfile(request.service_id());

        // Functional Errors
        if (profile.functionalError() != ServiceProfile.FunctionalErrorType.NONE) {
            return switch (profile.functionalError()) {
                case OPERATION_NOT_FOUND -> Response.status(404).entity("{\"error\": \"Operation Not Found\"}").build();
                case SERVICE_CANCELLED ->
                    Response.status(422).entity("{\"error\": \"Service Cancelled by Provider\"}").build();
                case DEBT_ANNULLED -> Response.status(422).entity("{\"error\": \"Debt Already Annulled\"}").build();
                case UNAUTHORIZED -> Response.status(401).entity("{\"error\": \"Unauthorized API Key\"}").build();
                case USER_NOT_FOUND -> Response.status(404).entity("{\"error\": \"Customer Not Found\"}").build();
                case LIMIT_EXCEEDED ->
                    Response.status(429).entity("{\"error\": \"Provider Rate Limit Exceeded\"}").build();
                default -> Response.ok(new ProviderPayResponse("ENDOSO-MOCK", "SUCCESS")).build();
            };
        }

        ProviderPayResponse res = new ProviderPayResponse(
                "ENDOSO-" + System.currentTimeMillis() + "-" + request.service_id() + "-OK", "SUCCESS");
        return Response.ok(res).build();
    }

    private void applySimulation(String serviceId) {
        ServiceProfile profile = ProfileResource.getProfile(serviceId);

        // 1. App Error (500)
        if (ThreadLocalRandom.current().nextDouble() < profile.appErrorRate()) {
            throw new WebApplicationException(
                    Response.serverError().entity("{\"error\": \"Internal Provider Error (Simulated)\"}").build());
        }

        // 2. Infra Error (503)
        if (ThreadLocalRandom.current().nextDouble() < profile.infraErrorRate()) {
            throw new WebApplicationException(
                    Response.status(Response.Status.SERVICE_UNAVAILABLE)
                            .entity("{\"error\": \"Connection Reset by Peer (Simulated)\"}").build());
        }

        // 3. Latency
        try {
            long millis = profile.p95Latency().toMillis();
            if (millis > 0) {
                // Add some jitter
                long sleepTime = (long) (millis * (0.8 + ThreadLocalRandom.current().nextDouble() * 0.4));
                Thread.sleep(sleepTime);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
