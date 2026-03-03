package com.bank.servicepayment.event;

import java.util.UUID;

public class PaymentSucceededEvent {
    public UUID transactionId;
    public String serviceId;
    public String customerReference;
    public Double amount;
    public String currency;
    public String timestamp;

    public PaymentSucceededEvent() {
    }

    public PaymentSucceededEvent(UUID transactionId, String serviceId, String customerReference, Double amount,
            String currency, String timestamp) {
        this.transactionId = transactionId;
        this.serviceId = serviceId;
        this.customerReference = customerReference;
        this.amount = amount;
        this.currency = currency;
        this.timestamp = timestamp;
    }
}
