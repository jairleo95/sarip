package com.bank.providersimulator.model;

import java.time.Duration;

public record ServiceProfile(
        String serviceId,
        String description,
        Duration p95Latency,
        double infraErrorRate, // 503, 504 (Connection, Timeout)
        double appErrorRate, // 500 (Internal Server Error)
        FunctionalErrorType functionalError // SCENARIO_NOT_FOUND, SERVICE_CANCELLED, etc.
) {
    public enum FunctionalErrorType {
        NONE,
        OPERATION_NOT_FOUND, // 404
        SERVICE_CANCELLED, // 422
        DEBT_ANNULLED, // 422
        UNAUTHORIZED, // 401
        USER_NOT_FOUND, // 404
        LIMIT_EXCEEDED // 429
    }
}
