# Sofyan OS v3.1 — Migration Fix

Ini adalah patch untuk error database setelah upgrade dari v1/v2 ke v3:

`column inbox_items.ai_type does not exist`

Penyebabnya: PostgreSQL lama dipertahankan (benar), tetapi `create_all()` tidak menambah kolom baru ke tabel lama.

Versi ini menambahkan migrasi startup yang aman dan idempotent:
- `inbox_items.ai_type`
- `inbox_items.ai_title`
- `projects.target_date`

Data lama tetap dipertahankan.

## Upgrade
1. Upload seluruh isi paket ini ke repo GitHub yang sama.
2. Commit/push ke branch `main`.
3. Di Coolify klik Redeploy.
4. Jangan hapus PostgreSQL volume.
5. Setelah app hidup, buka `https://app.ruanglegalitas.com`.

Migrasi dijalankan otomatis saat container app start.


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
