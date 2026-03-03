package com.bank.servicepayment.model;

import io.quarkus.hibernate.orm.panache.PanacheEntityBase;
import jakarta.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "accounts")
public class Account extends PanacheEntityBase {

    @Id
    @Column(name = "account_id")
    public String accountId;

    public String owner;

    @Column(nullable = false)
    public BigDecimal balance;

    @Column(nullable = false)
    public String currency;
}
