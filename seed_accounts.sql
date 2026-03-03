INSERT INTO accounts (account_id, balance, owner, currency) VALUES ('ACC-001', 1000000.00, 'Test User 1', 'USD') ON CONFLICT DO NOTHING;
INSERT INTO accounts (account_id, balance, owner, currency) VALUES ('ACC-002', 1000000.00, 'Test User 2', 'USD') ON CONFLICT DO NOTHING;
INSERT INTO accounts (account_id, balance, owner, currency) VALUES ('ACC-003', 1000000.00, 'Test User 3', 'USD') ON CONFLICT DO NOTHING;
INSERT INTO accounts (account_id, balance, owner, currency) VALUES ('ACC-004', 1000000.00, 'Test User 4', 'USD') ON CONFLICT DO NOTHING;
INSERT INTO accounts (account_id, balance, owner, currency) VALUES ('ACC-005', 1000000.00, 'Test User 5', 'USD') ON CONFLICT DO NOTHING;
