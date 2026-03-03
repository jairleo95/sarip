package com.bank.providersimulator.resource;

import com.bank.providersimulator.model.ServiceProfile;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Path("/api/v1/profiles")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class ProfileResource {

    // In-memory storage for hot reloading
    private static final Map<String, ServiceProfile> PROFILES = new ConcurrentHashMap<>();

    static {
        // Default Profiles
        PROFILES.put("DEFAULT", new ServiceProfile("DEFAULT", "Standard", Duration.ofMillis(100), 0.0, 0.0,
                ServiceProfile.FunctionalErrorType.NONE));
        PROFILES.put("E001", new ServiceProfile("E001", "Random Errors", Duration.ofMillis(200), 0.0, 0.01,
                ServiceProfile.FunctionalErrorType.NONE));
        PROFILES.put("E020", new ServiceProfile("E020", "High Latency", Duration.ofSeconds(2), 0.0, 0.0,
                ServiceProfile.FunctionalErrorType.NONE));
        PROFILES.put("E099", new ServiceProfile("E099", "Rate Limited", Duration.ofMillis(100), 0.0, 0.0,
                ServiceProfile.FunctionalErrorType.LIMIT_EXCEEDED));

        // Functional Error Examples
        PROFILES.put("FUNC-404", new ServiceProfile("FUNC-404", "Operation Not Found", Duration.ofMillis(100), 0.0, 0.0,
                ServiceProfile.FunctionalErrorType.OPERATION_NOT_FOUND));
        PROFILES.put("FUNC-422", new ServiceProfile("FUNC-422", "Service Cancelled", Duration.ofMillis(100), 0.0, 0.0,
                ServiceProfile.FunctionalErrorType.SERVICE_CANCELLED));
        PROFILES.put("FUNC-ANNULLED", new ServiceProfile("FUNC-ANNULLED", "Debt Annulled", Duration.ofMillis(100), 0.0,
                0.0, ServiceProfile.FunctionalErrorType.DEBT_ANNULLED));
        PROFILES.put("FUNC-USER-NOT-FOUND", new ServiceProfile("FUNC-USER-NOT-FOUND", "User Not Found",
                Duration.ofMillis(100), 0.0, 0.0, ServiceProfile.FunctionalErrorType.USER_NOT_FOUND));
    }

    public static ServiceProfile getProfile(String serviceId) {
        return PROFILES.getOrDefault(serviceId, PROFILES.get("DEFAULT"));
    }

    @GET
    public Map<String, ServiceProfile> getAll() {
        return PROFILES;
    }

    @GET
    @Path("/{id}")
    public Response get(@PathParam("id") String id) {
        ServiceProfile p = PROFILES.get(id);
        return p != null ? Response.ok(p).build() : Response.status(Response.Status.NOT_FOUND).build();
    }

    @POST
    public Response update(ServiceProfile profile) {
        PROFILES.put(profile.serviceId(), profile);
        return Response.ok(profile).build();
    }
}
