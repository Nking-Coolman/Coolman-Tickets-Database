from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


def build_qr_url(target_url: str, size: int) -> str:
    params = urlencode(
        {
            "text": target_url,
            "size": str(size),
            "format": "png",
            "margin": "2",
            "dark": "111111",
            "light": "ffffff",
        }
    )
    return f"https://quickchart.io/qr?{params}"


def write_qr_png(target_url: str, output_path: Path, size: int) -> None:
    qr_url = build_qr_url(target_url, size)
    with urlopen(qr_url, timeout=30) as response:
        image_bytes = response.read()
    output_path.write_bytes(image_bytes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a QR code PNG for a site URL.")
    parser.add_argument("url", help="The public URL to encode in the QR code.")
    parser.add_argument(
        "--output",
        default="coolman-ticket-portal-qr.png",
        help="PNG file path to write. Defaults to coolman-ticket-portal-qr.png in the current folder.",
    )
    parser.add_argument("--size", type=int, default=600, help="QR image size in pixels. Defaults to 600.")
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_qr_png(args.url, output_path, args.size)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())