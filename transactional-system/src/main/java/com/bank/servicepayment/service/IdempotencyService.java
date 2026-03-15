package com.bank.servicepayment.service;

import io.quarkus.redis.datasource.RedisDataSource;
import io.quarkus.redis.datasource.value.ValueCommands;
import jakarta.enterprise.context.ApplicationScoped;
import java.time.Duration;

@ApplicationScoped
public class IdempotencyService {

    private final ValueCommands<String, String> valueCommands;
    private static final Duration DEFAULT_TTL = Duration.ofHours(24);

    public IdempotencyService(RedisDataSource ds) {
        this.valueCommands = ds.value(String.class);
    }

    public boolean isProcessing(String key) {
        String value = valueCommands.get(key);
        return "PROCESSING".equals(value);
    }

    public String getStoredResponse(String key) {
        return valueCommands.get(key);
    }

    public void markAsProcessing(String key) {
        valueCommands.setex(key, DEFAULT_TTL.toSeconds(), "PROCESSING");
    }

    public void saveResult(String key, String responseJson) {
        valueCommands.setex(key, DEFAULT_TTL.toSeconds(), responseJson);
    }
}
