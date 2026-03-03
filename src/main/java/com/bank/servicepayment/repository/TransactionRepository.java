package com.bank.servicepayment.repository;

import com.bank.servicepayment.model.Transaction;
import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.UUID;

@ApplicationScoped
public class TransactionRepository implements PanacheRepositoryBase<Transaction, UUID> {
    public Transaction findByIdempotencyKey(String key) {
        return find("idempotencyKey", key).firstResult();
    }
}
