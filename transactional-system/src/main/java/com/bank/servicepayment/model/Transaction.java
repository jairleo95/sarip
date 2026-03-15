package com.bank.servicepayment.model;

import io.quarkus.hibernate.orm.panache.PanacheEntityBase;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "transactions")
public class Transaction extends PanacheEntityBase {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    public UUID id;

    @Column(name = "service_id", nullable = false)
    public String serviceId;

    @Column(name = "customer_reference", nullable = false)
    public String customerReference;

    @Column(nullable = false)
    public Double amount;

    public String currency;

    @Column(nullable = false)
    public String status;

    @Column(name = "idempotency_key", unique = true)
    public String idempotencyKey;

    @Column(name = "receipt_number")
    public String receiptNumber;

    @Column(name = "provider_endorsement")
    public String providerEndorsement;

    @Column(name = "target_account")
    public String targetAccount;

    @Column(name = "created_at", updatable = false)
    public LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "updated_at")
    public LocalDateTime updatedAt = LocalDateTime.now();
}
