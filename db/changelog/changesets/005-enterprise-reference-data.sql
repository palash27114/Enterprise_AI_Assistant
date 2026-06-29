--liquibase formatted sql

--changeset enterprise-ai:005-customers-table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    account_manager VARCHAR(255),
    region VARCHAR(100),
    mrr_usd INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'Active',
    since DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--changeset enterprise-ai:005-leave-requests-table
CREATE TABLE IF NOT EXISTS leave_requests (
    request_id VARCHAR(20) PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    days INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON leave_requests(employee_id);

--changeset enterprise-ai:005-workflow-definitions-table
CREATE TABLE IF NOT EXISTS workflow_definitions (
    workflow_key VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    steps JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--changeset enterprise-ai:005-workflow-executions-table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id VARCHAR(36) PRIMARY KEY,
    workflow_key VARCHAR(50) NOT NULL REFERENCES workflow_definitions(workflow_key) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'Triggered',
    context TEXT,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_key ON workflow_executions(workflow_key);

--changeset enterprise-ai:005-policies-table
CREATE TABLE IF NOT EXISTS policies (
    id SERIAL PRIMARY KEY,
    section VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL
);

--changeset enterprise-ai:005-seed-customers
INSERT INTO customers (customer_id, name, segment, account_manager, region, mrr_usd, status, since) VALUES
    ('CUST-5001', 'Acme Corporation', 'Enterprise', 'Emily Carter', 'North America', 12500, 'Active', '2020-04-12'),
    ('CUST-5002', 'Globex Industries', 'Mid-Market', 'David Foster', 'Europe', 4800, 'Active', '2022-09-03'),
    ('CUST-5003', 'Initech Labs', 'SMB', 'Emily Carter', 'APAC', 950, 'Trial', '2025-11-18')
ON CONFLICT (customer_id) DO NOTHING;

--changeset enterprise-ai:005-seed-leave-requests
INSERT INTO leave_requests (request_id, employee_id, days, status) VALUES
    ('LV-301', 'EMP-1071', 3, 'Approved'),
    ('LV-302', 'EMP-1002', 5, 'Pending')
ON CONFLICT (request_id) DO NOTHING;

--changeset enterprise-ai:005-seed-workflows
INSERT INTO workflow_definitions (workflow_key, name, steps) VALUES
    ('onboarding', 'Employee Onboarding', '["Create accounts", "Assign equipment", "Schedule orientation", "Grant app access"]'::jsonb),
    ('offboarding', 'Employee Offboarding', '["Revoke access", "Collect equipment", "Final payroll", "Exit interview"]'::jsonb),
    ('access_provisioning', 'Access Provisioning', '["Validate request", "Manager approval", "IT provisioning", "Audit log"]'::jsonb),
    ('leave_approval', 'Leave Approval', '["Submit request", "Manager review", "HR confirmation", "Calendar update"]'::jsonb),
    ('incident_escalation', 'Incident Escalation', '["Triage ticket", "Notify on-call", "Create war room", "Post-incident review"]'::jsonb)
ON CONFLICT (workflow_key) DO NOTHING;

--changeset enterprise-ai:005-seed-policies
INSERT INTO policies (section, summary) VALUES
    ('Leave Policy', '20 days annual leave, 10 sick days'),
    ('Remote Work', 'Hybrid schedule up to 3 days remote'),
    ('Expense Policy', 'Pre-approval required above $500');
