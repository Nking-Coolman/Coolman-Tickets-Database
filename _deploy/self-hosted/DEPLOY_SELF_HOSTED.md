Self-Hosted Server Publish
Generated: 2026-04-14

This folder runs the ticket site on your own small server with Docker Compose + Caddy.
It serves the bundle root two levels up from this folder.

Quick start on the server:
1. Copy this full always_on_site bundle onto the server.
2. Change into _deploy/self-hosted.
3. Copy .env.example to .env and set SITE_ADDRESS.
4. Run: docker compose up -d

Examples for SITE_ADDRESS:
- tickets.example.com  -> public HTTPS with automatic Caddy certificates
- :80                  -> plain HTTP on the server IP for private/VPN use or first-time testing

Notes:
- Caddy serves /index.html and /tickets-data.json with no-cache headers so refreshes show quickly.
- Preview PNGs are cached for 7 days because they are large and rarely change.
- Keep the site at the host root so /tickets-data.json and /ticket-previews/* work unchanged.