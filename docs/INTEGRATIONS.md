# Integrasi Sofyan OS v3

## Tujuan
Sofyan OS bukan pengganti semua tools. Ia menjadi command center yang menghubungkan tools yang sudah Anda bayar/pakai.

### Existing tools
- Coolify/VPS: deployment
- PostgreSQL: data pusat
- n8n: automation/orchestration
- Telegram: universal capture + command
- StarSender: WhatsApp transport & webhook
- KIRIM.EMAIL: email marketing/transactional
- ChatGPT/OpenAI API: reasoning/classification/drafting
- IG/FB: distribution & lead source (via Meta API bila kredensial tersedia)
- Website/domain: interface publik/internal

## n8n environment variables
Set pada n8n:
- SOFYAN_OS_URL=https://app.ruanglegalitas.com
- SOFYAN_OS_API_KEY=<API_KEY dari Coolify Sofyan OS>
- TELEGRAM_BOT_TOKEN=<token bot>
- TELEGRAM_CHAT_ID=<chat id Anda>

Import seluruh JSON di folder `n8n-workflows`.

## StarSender
Arahkan webhook StarSender ke Production Webhook URL workflow:
`Sofyan OS - StarSender Inbound`.

StarSender resmi mendukung webhook pesan masuk realtime. Payload umum berisi message/from/timestamp; webhook premium juga menyediakan device/device_name/push_name dan metadata lain.

## KIRIM.EMAIL
Tidak perlu mengganti Kirim.Email. Gunakan sebagai email transport.
Tambahkan credential/API di n8n saat workflow email mulai diaktifkan.

## Instagram/Facebook
Jangan scraping akun. Integrasi production menggunakan Meta Graph API/webhook. Diperlukan Meta App dan token/permission terkait. Sampai kredensial tersedia, Sofyan OS tetap menjadi content planning/source-of-truth.

## AI
ChatGPT subscription dan OpenAI API adalah dua hal berbeda.
Untuk automation backend, isi OPENAI_API_KEY atau gunakan credential AI yang sudah ada di n8n.
Tanpa API key, seluruh fungsi core tetap berjalan; AI classification hanya nonaktif.

## Prinsip
- Communication tetap di kanal aslinya.
- Action masuk Inbox/Task.
- Lead masuk CRM.
- Transaksi masuk Finance.
- Pengetahuan masuk Knowledge.
- Konten masuk Content.
- Hanya maksimal 3 Highlight.
