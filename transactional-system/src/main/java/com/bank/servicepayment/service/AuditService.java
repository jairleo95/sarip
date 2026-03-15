package com.bank.servicepayment.service;

import com.bank.servicepayment.util.EncryptionService;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.reactive.messaging.Channel;
import org.eclipse.microprofile.reactive.messaging.Emitter;

import java.util.HashMap;
import java.util.Map;

@ApplicationScoped
public class AuditService {

    @Inject
    EncryptionService encryptionService;

    @Inject
    ObjectMapper objectMapper;

    @Inject
    @Channel("audit-events")
    Emitter<String> auditEmitter;

    public void sendAuditEvent(String operation, Object request, Object response, Map<String, Object> metadata) {
        try {
            Map<String, Object> auditLog = new HashMap<>();
            auditLog.put("operation", operation);
            auditLog.put("request", request);
            auditLog.put("response", response);
            auditLog.put("metadata", metadata);
            auditLog.put("timestamp", System.currentTimeMillis());

            String jsonPayload = objectMapper.writeValueAsString(auditLog);
            String encryptedPayload = encryptionService.encrypt(jsonPayload);

            auditEmitter.send(encryptedPayload);
            System.out.println("[AuditService] Encrypted audit event sent for: " + operation);
        } catch (Exception e) {
            System.err.println("[AuditService] Failed to send audit event: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
