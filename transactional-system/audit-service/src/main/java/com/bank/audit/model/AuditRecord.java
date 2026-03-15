package com.bank.audit.model;

import io.quarkus.mongodb.panache.common.MongoEntity;
import io.quarkus.mongodb.panache.PanacheMongoEntity;

import java.time.LocalDateTime;

@MongoEntity(collection = "audit_records")
public class AuditRecord extends PanacheMongoEntity {
    public String encryptedPayload;
    public LocalDateTime savedAt;

    public AuditRecord() {
    }

    public AuditRecord(String encryptedPayload) {
        this.encryptedPayload = encryptedPayload;
        this.savedAt = LocalDateTime.now();
    }
}
