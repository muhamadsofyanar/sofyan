# Sofyan OS

Command center pribadi untuk Muhamad Sofyan AR.

Domain target: `app.ruanglegalitas.com`

Versi ini sengaja fokus pada fondasi:
- Inbox / capture
- Task
- Highlight maksimal 3
- Project
- Keuangan
- Debt Exit
- 3 area: Pribadi, STIFIn, IZINHUKUM
- API capture untuk n8n
- Login admin
- PostgreSQL
- Docker Compose

## Upload ke GitHub

Buat repository baru, lalu upload seluruh isi folder ini.

## Install dari GitHub di VPS

```bash
git clone https://github.com/USERNAME/NAMA-REPO.git
cd NAMA-REPO
cp .env.example .env
nano .env
```

Ubah minimal:
- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `POSTGRES_PASSWORD`
- `DATABASE_URL` agar password DB sama
- `API_KEY`

Lalu:

```bash
chmod +x install.sh
./install.sh
```

App berjalan lokal di:

```text
http://127.0.0.1:8088
```

## Nginx

Template tersedia:

```text
deploy/nginx-app.ruanglegalitas.com.conf
```

Contoh pemasangan:

```bash
sudo cp deploy/nginx-app.ruanglegalitas.com.conf /etc/nginx/sites-available/app.ruanglegalitas.com
sudo ln -s /etc/nginx/sites-available/app.ruanglegalitas.com /etc/nginx/sites-enabled/app.ruanglegalitas.com
sudo nginx -t
sudo systemctl reload nginx
```

Jika Certbot sudah tersedia:

```bash
sudo certbot --nginx -d app.ruanglegalitas.com
```

## Integrasi n8n

Endpoint capture:

```text
POST https://app.ruanglegalitas.com/api/capture
Header: X-API-Key: <API_KEY>
Content-Type: application/json
```

Body:

```json
{
  "text": "Follow up promotor A",
  "area": "stifin",
  "source": "n8n"
}
```

`area` yang tersedia:
- `personal`
- `stifin`
- `izinhukum`
