# Sofyan OS v3 — Ecosystem

Paket ini adalah upgrade dari v2 Full.

Termasuk:
- Sofyan OS app
- PostgreSQL
- Inbox/Task/Highlight/Project/Dependencies
- Finance & Debt Exit
- CRM STIFIn + IZINHUKUM
- Content/Branding
- Knowledge/E-course
- Telegram
- AI classification
- StarSender inbound
- API untuk n8n
- 6 workflow n8n siap import
- integrasi architecture docs

## Upgrade
Upload seluruh isi repo ke GitHub yang sama lalu Redeploy di Coolify.
Jangan hapus volume PostgreSQL.

## Setelah redeploy
1. Tambahkan env Telegram/OpenAI bila belum.
2. Import seluruh JSON dari `n8n-workflows/`.
3. Set env n8n sesuai `docs/INTEGRATIONS.md`.
4. Arahkan StarSender webhook ke workflow n8n StarSender.

Baca:
- `docs/OPERATING-SYSTEM.md`
- `docs/INTEGRATIONS.md`
