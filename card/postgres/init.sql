-- PostgreSQL initialization script for Transport Cards Accounting System
-- Run: psql -U postgres -d transport_cards -f init.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLE: card_types
-- =====================================================
CREATE TABLE IF NOT EXISTS card_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    print_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: owners
-- =====================================================
CREATE TABLE IF NOT EXISTS owners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: applicants
-- =====================================================
CREATE TABLE IF NOT EXISTS applicants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: organizations
-- =====================================================
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: mfcs
-- =====================================================
CREATE TABLE IF NOT EXISTS mfcs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: employees
-- =====================================================
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(500) NOT NULL,
    login VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    roles JSONB DEFAULT '["user"]',
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: cards
-- =====================================================
CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_number VARCHAR(19) UNIQUE NOT NULL,
    card_type_id UUID REFERENCES card_types(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT '',
    owner_id UUID REFERENCES owners(id) ON DELETE SET NULL,
    applicant_id UUID REFERENCES applicants(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cards_number ON cards(card_number);
CREATE INDEX IF NOT EXISTS idx_cards_status ON cards(status);
CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(card_type_id);

-- =====================================================
-- TABLE: documents
-- =====================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_type VARCHAR(50) NOT NULL,
    doc_number VARCHAR(50) NOT NULL,
    doc_date DATE NOT NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    mfc_id UUID REFERENCES mfcs(id) ON DELETE SET NULL,
    employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    lines JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'draft',
    created_by UUID REFERENCES employees(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP,
    posted_by UUID REFERENCES employees(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(doc_date);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- =====================================================
-- TABLE: action_log
-- =====================================================
CREATE TABLE IF NOT EXISTS action_log (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_action_log_user ON action_log(user_id);
CREATE INDEX IF NOT EXISTS idx_action_log_timestamp ON action_log(timestamp);

-- =====================================================
-- TABLE: constants
-- =====================================================
CREATE TABLE IF NOT EXISTS constants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_name VARCHAR(500) DEFAULT 'ООО Транспортные Карты'
);

-- =====================================================
-- TABLE: counters
-- =====================================================
CREATE TABLE IF NOT EXISTS counters (
    prefix VARCHAR(20) PRIMARY KEY,
    value INTEGER DEFAULT 1
);

-- =====================================================
-- DEFAULT DATA
-- =====================================================
INSERT INTO employees (id, full_name, login, password, roles, permissions)
VALUES (
    uuid_generate_v4(),
    'Администратор',
    'admin',
    'admin',
    '["admin"]',
    '{}'
)
ON CONFLICT (login) DO NOTHING;

INSERT INTO constants (organization_name)
VALUES ('ООО Транспортные Карты')
ON CONFLICT DO NOTHING;

INSERT INTO counters (prefix, value)
VALUES ('DOC', 1)
ON CONFLICT (prefix) DO NOTHING;
