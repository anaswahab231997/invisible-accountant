-- Migration 004: Add Practice Multi-Tenancy and Partner Portal Tables

-- 1. Practices Table (Accountancy Firms)
CREATE TABLE IF NOT EXISTS practices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    firm_code VARCHAR(20) UNIQUE NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) UNIQUE NOT NULL,
    contact_phone VARCHAR(50),
    company_number VARCHAR(50),
    regulatory_body VARCHAR(50) DEFAULT 'ICAEW',
    regulatory_number VARCHAR(100),
    logo_url TEXT,
    primary_accounting_platform VARCHAR(50) DEFAULT 'XERO',
    commission_rate_gbp NUMERIC(10, 2) DEFAULT 3.00,
    password_hash VARCHAR(255),
    api_key_hash VARCHAR(128),
    bacs_sort_code VARCHAR(10),
    bacs_account_number VARCHAR(20),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Practice Clients Mapping Table
CREATE TABLE IF NOT EXISTS practice_clients (
    id SERIAL PRIMARY KEY,
    practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
    client_sender_id VARCHAR(100) NOT NULL,
    client_name VARCHAR(255),
    client_email VARCHAR(255),
    xero_tenant_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_receipt_at TIMESTAMP WITH TIME ZONE,
    total_receipts_count INTEGER DEFAULT 0,
    CONSTRAINT uq_practice_client UNIQUE (practice_id, client_sender_id)
);

-- 3. Practice Pilot Letters of Intent (LOIs) Table
CREATE TABLE IF NOT EXISTS practice_lois (
    id SERIAL PRIMARY KEY,
    practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
    signatory_name VARCHAR(255) NOT NULL,
    signatory_title VARCHAR(100) NOT NULL,
    firm_legal_name VARCHAR(255) NOT NULL,
    firm_crn VARCHAR(50),
    firm_address TEXT,
    pledged_client_seats INTEGER NOT NULL DEFAULT 50,
    pilot_duration_days INTEGER DEFAULT 90,
    commercial_terms_accepted BOOLEAN DEFAULT TRUE,
    signature_data_url TEXT NOT NULL,
    signature_ip_address VARCHAR(50) NOT NULL,
    signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    document_sha256 VARCHAR(64) NOT NULL,
    status VARCHAR(50) DEFAULT 'EXECUTED'
);

-- 4. Partner Commission Ledger
CREATE TABLE IF NOT EXISTS partner_commissions (
    id SERIAL PRIMARY KEY,
    practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
    billing_period VARCHAR(7) NOT NULL,
    active_clients_count INTEGER NOT NULL DEFAULT 0,
    total_receipts_processed INTEGER NOT NULL DEFAULT 0,
    rate_per_client_gbp NUMERIC(10, 2) NOT NULL DEFAULT 3.00,
    total_accrued_gbp NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    payout_status VARCHAR(50) DEFAULT 'ACCRUED',
    paid_at TIMESTAMP WITH TIME ZONE,
    payment_reference VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_practice_period UNIQUE (practice_id, billing_period)
);

-- 5. Add practice_id foreign keys to hmrc_ledger and chat_sessions
ALTER TABLE hmrc_ledger ADD COLUMN IF NOT EXISTS practice_id INTEGER REFERENCES practices(id) ON DELETE SET NULL;
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS practice_id INTEGER REFERENCES practices(id) ON DELETE SET NULL;

-- 6. Indexes for performant lookup
CREATE INDEX IF NOT EXISTS idx_practices_slug ON practices(slug);
CREATE INDEX IF NOT EXISTS idx_practices_firm_code ON practices(firm_code);
CREATE INDEX IF NOT EXISTS idx_practice_clients_sender ON practice_clients(client_sender_id);
CREATE INDEX IF NOT EXISTS idx_practice_clients_practice ON practice_clients(practice_id);
CREATE INDEX IF NOT EXISTS idx_hmrc_ledger_practice ON hmrc_ledger(practice_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_practice ON chat_sessions(practice_id);
