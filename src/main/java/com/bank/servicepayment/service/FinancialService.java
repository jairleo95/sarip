package com.bank.servicepayment.service;

import com.bank.servicepayment.model.Account;
import com.bank.servicepayment.model.LedgerEntry;
import com.bank.servicepayment.repository.AccountRepository;
import com.bank.servicepayment.repository.LedgerEntryRepository;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import java.math.BigDecimal;
import java.util.UUID;

@ApplicationScoped
public class FinancialService {

    @Inject
    AccountRepository accountRepository;

    @Inject
    LedgerEntryRepository ledgerEntryRepository;

    @Transactional
    public void processDebit(String accountId, BigDecimal amount, UUID transactionId) {
        Account account = accountRepository.findById(accountId);
        if (account == null) {
            throw new RuntimeException("Account not found: " + accountId);
        }

        if (account.balance.compareTo(amount) < 0) {
            throw new RuntimeException("Insufficient funds in account: " + accountId);
        }

        // 1. Update Account Balance
        account.balance = account.balance.subtract(amount);
        accountRepository.persist(account);

        // 2. Record Ledger Entry (Immutable Audit)
        LedgerEntry entry = new LedgerEntry();
        entry.transactionId = transactionId;
        entry.accountId = accountId;
        entry.amount = amount;
        entry.type = LedgerEntry.EntryType.DEBIT;
        ledgerEntryRepository.persist(entry);
    }
}
