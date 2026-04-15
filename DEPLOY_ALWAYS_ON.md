# Public Static Ticket Portal Deployment

Generated: 2026-04-14

Included files:

- index.html
- tickets-data.json
- ticket-previews/ (1861 PNG files)
- _deploy/object-storage/*
- _deploy/self-hosted/*

Recommended long-term hosting for a growing archive:

1. Object storage + CDN/custom domain (Cloudflare R2, Backblaze B2, S3-compatible storage)
2. Your own small web server or VM with Caddy/Nginx
3. Any static host only if its storage and bandwidth limits fit your archive

Important:

- This bundle is host-neutral. You can move it between hosts without changing code.
- Free-tier website products often have hard limits. For larger growth, prefer storage + CDN or your own server.
- Host the bundle at the site root so /tickets-data.json and /ticket-previews/* work unchanged.
- Generated publish helpers are under _deploy/ for both scalable hosting tracks.

After you get the final public URL:
Run this command to set URL + regenerate QR:

  .venv\Scripts\python.exe DataAnalysisExpert\generate_qr.py "<YOUR_PUBLIC_URL>" --output DataAnalysisExpert\coolman-ticket-portal-qr.png

Current portal_public_url in settings:

<https://nking-coolman.github.io/Tickets-Database/?v=20260415-1023>
