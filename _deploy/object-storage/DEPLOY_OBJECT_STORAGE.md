Object Storage Publish
Generated: 2026-04-14

Use this when you want the ticket site on S3-compatible storage with a CDN or custom domain.
Examples: Cloudflare R2, Backblaze B2 (S3 API), AWS S3, MinIO.

Important:
- The site expects to live at the host root so /tickets-data.json and /ticket-previews/* resolve unchanged.
- If you use a CDN or custom domain, point the domain root at this bucket/container output.
- The helper script excludes the _deploy folder from upload.

Typical publish command:
  ./publish_to_s3_compatible.ps1 -Bucket <bucket-name> -EndpointUrl <optional-endpoint> -PublicUrl https://tickets.example.com

Examples:
  Cloudflare R2:
    ./publish_to_s3_compatible.ps1 -Bucket coolman-tickets -EndpointUrl https://<account-id>.r2.cloudflarestorage.com -PublicUrl https://tickets.example.com
  Backblaze B2 S3:
    ./publish_to_s3_compatible.ps1 -Bucket coolman-tickets -EndpointUrl https://s3.us-west-004.backblazeb2.com -PublicUrl https://tickets.example.com
  AWS S3:
    ./publish_to_s3_compatible.ps1 -Bucket coolman-tickets -Region ca-central-1 -PublicUrl https://tickets.example.com

Prerequisites:
- AWS CLI installed and already authenticated for your provider.
- The bucket/container already exists and is fronted by your public hostname or CDN.
- The public hostname should serve this bundle from the root path.