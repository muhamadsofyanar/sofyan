# Sofyan OS v2 Full

Satu deployment untuk:
1. Inbox universal
2. Task & Highlight LuTug
3. Project
4. Dependencies
5. Finance
6. Debt Exit
7. CRM STIFIn
8. CRM IZINHUKUM
9. Content / Branding
10. Knowledge / E-course
11. Telegram capture
12. AI classification opsional
13. Executive summary API

## Upgrade
Upload seluruh isi repo ini menggantikan repo lama, lalu redeploy di Coolify.

Environment baru yang perlu ditambahkan:
```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_CHAT_ID=
TELEGRAM_WEBHOOK_SECRET=buat-random-sendiri
TELEGRAM_WEBHOOK_URL=https://app.ruanglegalitas.com/api/telegram/webhook
```

Setelah redeploy:
- App tetap di port 8080.
- Data PostgreSQL lama tetap memakai volume lama jika service/volume deployment tidak dihapus.
- Aktifkan Telegram webhook melalui `POST /api/telegram/setup` dengan header `X-API-Key`.

Endpoint n8n:
- `GET /api/daily-review`
- `GET /api/executive-summary`
- `POST /api/capture`
