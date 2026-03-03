# Encryption at Rest — Legal AI Tool (Task 9.3)

This document describes the encryption-at-rest strategy for the Legal AI Tool deployment.

## PostgreSQL — TLS in Transit + Application-Level Column Encryption

### TLS on all Postgres connections

`infra/postgres/postgresql.conf` enables `ssl = on` so every client connection
(Node API, Python agent backend) uses TLS 1.2+. Plain-text connections are
rejected.

### Sensitive column encryption (pgcrypto)

For columns containing PII (e.g. `users.email`, `audit_logs.metadata`), use
the **pgcrypto** extension with AES-256-CBC:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Store encrypted
UPDATE users
SET    email = pgp_sym_encrypt(email, current_setting('app.encryption_key'));

-- Read decrypted
SELECT pgp_sym_decrypt(email::bytea, current_setting('app.encryption_key'))
FROM   users
WHERE  id = $1;
```

Set `app.encryption_key` via a Postgres parameter (loaded from a secrets manager).

### Transparent Data Encryption (TDE) options

| Option | Notes |
|--------|-------|
| **LUKS/dm-crypt** (Linux host) | Encrypt the entire Docker volume at the block-device level. Zero Postgres changes. Requires root on host. |
| **AWS RDS storage encryption** | Enabled at cluster creation; uses AES-256. No application changes. |
| **Azure Database for PostgreSQL** | AES-256 by default; BYOK available. |
| **pg_tde extension** (PostgreSQL 17+) | Per-table TDE without OS-level encryption. |

## MongoDB — Encrypted Storage Engine

MongoDB Enterprise supports **Encrypted Storage Engine** (AES-256-CBC/GCM).
For the Community edition (used in local dev), enable LUKS on the Docker volume
or use a managed Atlas deployment with encryption at rest.

## Pinecone

Pinecone encrypts all index data at rest by default (AES-256).
No additional configuration is required.

## Verification

Run `infra/scripts/verify_encryption.sh` to check that:
1. The `postgresql.conf` file enables `ssl = on`.
2. The docker-compose volume is configured.
3. The TLS certificate files are referenced correctly.
