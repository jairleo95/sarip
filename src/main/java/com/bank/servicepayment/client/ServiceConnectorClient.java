package com.bank.servicepayment.client;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@RegisterRestClient(configKey = "connector-service")
@Path("/")
public interface ServiceConnectorClient {

    @POST
    @Path("/provider-debt")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    ProviderDebtResponse getDebt(ProviderDebtRequest request);

    @POST
    @Path("/provider-pay")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    ProviderPayResponse confirmPayment(ProviderPayRequest request);

    class ProviderDebtRequest {
        public String service_id;
        public String reference;
    }

    class ProviderDebtResponse {
        public Double amount;
        public String currency;
        public String target_account;
        public String description;
    }

    class ProviderPayRequest {
        public String service_id;
        public String transaction_id;
        public Double amount;
        public String reference;
    }

    class ProviderPayResponse {
        public String endorsement;
        public String status;
    }
}
