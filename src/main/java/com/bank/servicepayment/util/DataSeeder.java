package com.bank.servicepayment.util;

import com.bank.servicepayment.model.Account;
import com.bank.servicepayment.repository.AccountRepository;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import java.math.BigDecimal;

@ApplicationScoped
public class DataSeeder {

    @Inject
    AccountRepository accountRepository;

    @Transactional
    public void onStart(@Observes StartupEvent ev) {
        if (accountRepository.count() == 0) {
            Account testAccount = new Account();
            testAccount.accountId = "ACC-123456";
            testAccount.owner = "John Doe";
            testAccount.balance = new BigDecimal("1000.00");
            testAccount.currency = "USD";
            accountRepository.persist(testAccount);

            Account testAccount2 = new Account();
            testAccount2.accountId = "ACC-789";
            testAccount2.owner = "Jane Smith";
            testAccount2.balance = new BigDecimal("50.00"); // Low balance for testing failure
            testAccount2.currency = "USD";
            accountRepository.persist(testAccount2);
        }
    }
}
