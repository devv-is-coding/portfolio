# Deployment

How to put the portfolio online. The hosting choice is still open (decision D8 in the plan); this guide covers the two options and what each needs. Replace `example.com` with your domain.

```
Visitor ──HTTPS──> Next.js (pages, admin, Server Actions) ──> FastAPI ──> MariaDB, Redis
                                                                  └──> Celery worker (emails, ImageKit cleanup, token cleanup)
Browser ──> ImageKit (images, admin uploads)
```

The browser never calls the API: pages are rendered by Next.js, forms post to Next.js Server Actions, and admin tokens stay in httpOnly cookies on the Next.js server. So the API needs no CORS origins and doesn't have to be public.

## Option A: one server (recommended)

Everything runs on one small Linux server with Docker: the existing production images (`compose.prod.yaml`) plus `deploy/vps/compose.vps.yaml`, which adds Caddy for HTTPS and the production settings. The backend idles at about 280 MB, so 1 vCPU and 1-2 GB of RAM are enough.

What the override does (all tested locally through Caddy, in production mode):

- **Caddy is the only public entry** (ports 80 and 443) and gets the HTTPS certificate itself. The API and the Next.js server aren't published.
- **Visitor IPs are trusted along one path only:** Caddy writes the visitor's address into `X-Forwarded-For` (dropping any value the visitor sent), Next.js forwards it, and the API trusts it from the Next.js server's fixed address (`FORWARDED_ALLOW_IPS=172.31.240.10`). The login and contact limits then count each visitor. A forged header is ignored.
- **Production mode:** `ENVIRONMENT=production` (the API refuses the development JWT key and non-HTTPS origins), JSON logs, no CORS origins, real database passwords required, and every service restarts after a crash or reboot.

### Steps

1. **Server:** Ubuntu 24.04 (or similar) with Docker Engine and the Compose plugin. Open ports 22, 80 and 443 only.
2. **DNS:** an `A` (and `AAAA`) record for `example.com` pointing at the server.
3. **Code:** `git clone https://github.com/devv-is-coding/portfolio.git` and `cd portfolio`.
4. **Secrets for Compose:** a `.env` file in the repo root (gitignored), read by Docker Compose:

   ```dotenv
   SITE_DOMAIN=example.com
   DB_PASSWORD=<long random password>
   DB_ROOT_PASSWORD=<another long random password>
   ```

5. **Backend settings:** `backend/.env` from `backend/.env.example` with the production values in the table below.
6. **Start:**

   ```bash
   docker compose -f compose.prod.yaml -f deploy/vps/compose.vps.yaml up -d --build
   ```

   Migrations run on every start (`migrate` service). Caddy requests the certificate on the first visit.
7. **Admin account:**

   ```bash
   docker compose -f compose.prod.yaml -f deploy/vps/compose.vps.yaml exec backend python -m app.commands.create_admin --email you@example.com
   ```

8. **Check** (see "After deploying" below).

**Updates:** `git pull`, then the same `up -d --build` command. **Backups:** ImageKit keeps the files; back up the database daily, for example `docker compose ... exec -T mariadb mariadb-dump -uroot -p"$DB_ROOT_PASSWORD" portfolio | gzip > backup-$(date +%F).sql.gz` from cron, and copy it off the server.

## Option B: frontend on Vercel, backend on a server

The Next.js app on Vercel (project root `frontend`), the backend on a server as in option A, with Caddy serving the API on a subdomain (`api.example.com { reverse_proxy backend:8000 }`).

- **Vercel environment variables:** `API_URL=https://api.example.com` (Production and Preview). It must be reachable during the build, so pages prerender with their data; without it the build reads data per request instead.
- **Open issue, before going live:** Vercel calls the API from changing addresses, so `FORWARDED_ALLOW_IPS` can't name them. The login and contact limits would then count Vercel's addresses instead of visitors (one attacker could lock the admin login for everyone), and trusting all addresses would let anyone fake theirs. This option needs a small backend change first: the Next.js server signs the visitor address with a shared secret, and the API trusts the address only with that secret.
- `/docs` stays public on the API domain (decision D7); admin routes still need a token.

## Settings

### `backend/.env` (production)

| Variable | Value |
|---|---|
| `JWT_SECRET_KEY` | A long random value, e.g. `openssl rand -base64 48`. The API refuses to start with the development key. |
| `IMAGEKIT_PUBLIC_KEY`, `IMAGEKIT_PRIVATE_KEY`, `IMAGEKIT_URL_ENDPOINT` | From the ImageKit dashboard; required in production. A custom ImageKit domain must also be added to the CSP in `frontend/next.config.ts`. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_STARTTLS`, `SMTP_FROM`, `CONTACT_NOTIFY_EMAIL` | Optional: email notice for new contact messages. |
| `SENTRY_DSN` | Optional: error reporting. |
| `WEB_CONCURRENCY` | Optional: more API processes (see `backend/README.md`); 1 is enough for a portfolio. |

`ENVIRONMENT`, `LOG_FORMAT`, `CORS_ORIGINS`, `DB_*`, `REDIS_URL` and `FORWARDED_ALLOW_IPS` are set by the compose files; don't put them in `backend/.env`.

### Frontend

| Variable | Value |
|---|---|
| `API_URL` | Where the Next.js server reaches the API: `http://backend:8000` on one server (set in `compose.prod.yaml`), `https://api.example.com` on Vercel. |

`NEXT_PUBLIC_API_URL` is still passed to the image build but no code uses it: the browser never calls the API.

## After deploying

- `https://example.com/` and `/admin/login` answer 200 over HTTPS; `http://` redirects to `https://`.
- Response headers: `curl -I https://example.com/` shows `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options` and no `X-Powered-By`.
- Sign in, publish a project: it appears on the site at once. Send the contact form: it appears in the admin inbox with your own IP address (not the server's).
- Lighthouse against the live site: `cd frontend && LHCI_BASE_URL=https://example.com npx --yes @lhci/cli@0.15.1 autorun --config=lighthouserc.js`.
- API load test from another machine, against the production hosting (see `backend/README.md`, "Performance").
