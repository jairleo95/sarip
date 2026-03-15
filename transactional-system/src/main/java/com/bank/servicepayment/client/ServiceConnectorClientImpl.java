package com.bank.servicepayment.client;

import jakarta.enterprise.context.ApplicationScoped;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.inject.Inject;

@ApplicationScoped
public class ServiceConnectorClientImpl implements ServiceConnectorClient {
    
    @Inject
    ObjectMapper mapper;

    private HttpClient client = HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();
    private String baseUri = "http://provider-simulator:8084/mock-provider";

    @Override
    public ProviderDebtResponse getDebt(ProviderDebtRequest request) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(baseUri + "/provider-debt"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(request)))
                .build();
            HttpResponse<String> res = client.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() >= 400) throw new RuntimeException("Provider HTTP status: " + res.statusCode());
            return mapper.readValue(res.body(), ProviderDebtResponse.class);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public ProviderPayResponse confirmPayment(ProviderPayRequest request) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(baseUri + "/provider-pay"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(request)))
                .build();
            HttpResponse<String> res = client.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() >= 400) throw new RuntimeException("Provider HTTP status: " + res.statusCode());
            return mapper.readValue(res.body(), ProviderPayResponse.class);
        } catch (Exception e) {
            throw new RuntimeException("Connection refused: Native client exception: " + e.getMessage(), e);
        }
    }
}
