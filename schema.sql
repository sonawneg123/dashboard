-- ================================================================
--  Three-Tier User Management App — MySQL RDS Schema
--  Engine  : MySQL 8.0+
--  Database: usermanagement
-- ================================================================

CREATE DATABASE IF NOT EXISTS usermanagement
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE usermanagement;

-- ── Users ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name        VARCHAR(120)     NOT NULL,
    email       VARCHAR(255)     NOT NULL,
    phone       VARCHAR(20)          NULL,
    role        ENUM('admin','editor','viewer') NOT NULL DEFAULT 'viewer',
    status      ENUM('active','inactive','banned') NOT NULL DEFAULT 'active',
    avatar_url  VARCHAR(512)         NULL,
    created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_users          PRIMARY KEY (id),
    CONSTRAINT uq_users_email    UNIQUE      (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Audit Log ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    user_id     BIGINT UNSIGNED      NULL,
    action      VARCHAR(50)      NOT NULL,   -- CREATE | UPDATE | DELETE
    table_name  VARCHAR(64)      NOT NULL,
    record_id   BIGINT UNSIGNED      NULL,
    old_data    JSON                 NULL,
    new_data    JSON                 NULL,
    ip_address  VARCHAR(45)          NULL,
    created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_audit PRIMARY KEY (id),
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Health-check table (ALB target group health) ─────────────────
CREATE TABLE IF NOT EXISTS healthcheck (
    id          INT              NOT NULL DEFAULT 1,
    status      VARCHAR(10)      NOT NULL DEFAULT 'ok',
    checked_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_health PRIMARY KEY (id)
) ENGINE=InnoDB;

INSERT INTO healthcheck (id, status) VALUES (1, 'ok')
  ON DUPLICATE KEY UPDATE status = 'ok';

-- ── Indexes ──────────────────────────────────────────────────────
CREATE INDEX idx_users_status     ON users (status);
CREATE INDEX idx_users_role       ON users (role);
CREATE INDEX idx_users_created_at ON users (created_at DESC);
CREATE INDEX idx_audit_action     ON audit_log (action);
CREATE INDEX idx_audit_created    ON audit_log (created_at DESC);

-- ── Seed data ────────────────────────────────────────────────────
INSERT INTO users (name, email, phone, role, status) VALUES
  ('Alice Johnson',  'alice@example.com',  '+1-555-0101', 'admin',  'active'),
  ('Bob Martinez',   'bob@example.com',    '+1-555-0102', 'editor', 'active'),
  ('Carol Singh',    'carol@example.com',  '+1-555-0103', 'viewer', 'active'),
  ('David Lee',      'david@example.com',  '+1-555-0104', 'editor', 'inactive'),
  ('Eva Müller',     'eva@example.com',    '+1-555-0105', 'viewer', 'active');

-- ── Stored procedure: full-text search ──────────────────────────
DELIMITER $$
CREATE PROCEDURE search_users(IN p_query VARCHAR(255))
BEGIN
    SET p_query = CONCAT('%', p_query, '%');
    SELECT * FROM users
    WHERE  name LIKE p_query
        OR email LIKE p_query
        OR phone LIKE p_query
    ORDER BY created_at DESC;
END$$
DELIMITER ;
