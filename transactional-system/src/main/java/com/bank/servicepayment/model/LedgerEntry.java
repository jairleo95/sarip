package com.bank.servicepayment.model;

import io.quarkus.hibernate.orm.panache.PanacheEntityBase;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "ledger_entries")
public class LedgerEntry extends PanacheEntityBase {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    public UUID id;

    @Column(name = "transaction_id", nullable = false)
    public UUID transactionId;

    @Column(name = "account_id", nullable = false)
    public String accountId;

    @Column(nullable = false)
    public BigDecimal amount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    public EntryType type;

    @Column(name = "created_at")
    public LocalDateTime createdAt = LocalDateTime.now();

    public enum EntryType {
        DEBIT, CREDIT
    }
}
