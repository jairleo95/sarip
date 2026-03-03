package com.bank.servicepayment.repository;

import com.bank.servicepayment.model.Account;
import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class AccountRepository implements PanacheRepositoryBase<Account, String> {
}
