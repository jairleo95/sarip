package com.bank.audit.consumer;

import com.bank.audit.model.AuditRecord;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.transaction.Transactional;
import org.eclipse.microprofile.reactive.messaging.Incoming;
import io.smallrye.reactive.messaging.annotations.Blocking;

@ApplicationScoped
public class AuditConsumer {

    @Incoming("audit-events")
    @Blocking
    public void consume(String encryptedPayload) {
        try {
            AuditRecord record = new AuditRecord(encryptedPayload);
            record.persist();
            System.out.println("[AuditConsumer] Secure audit record persisted to MongoDB: "
                    + encryptedPayload.substring(0, Math.min(20, encryptedPayload.length())) + "...");
        } catch (Exception e) {
            System.err.println("[AuditConsumer] Error persisting audit record: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
