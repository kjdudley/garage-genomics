#!/usr/bin/env python3
"""
Create the "Garage Genomics" group on LibreBiotech via the REST API.

Creator is automatically added as the first Leader.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python create_group.py --dry-run   # show payload
    python create_group.py             # POST /groups

API reference: https://librebiotech.org/?action=docs&page=api#groups
"""

import argparse
import json
import os
import sys

import requests

API_BASE = "https://librebiotech.org/api.php/v1"

GROUP = {
    "name": "Garage Genomics",
    "description": (
        "Umbrella group for the garage-genomics public video series "
        "(https://github.com/kjdudley/garage-genomics) — citizen-science "
        "projects teaching accessible molecular biology on a Raspberry Pi: "
        "DNA barcoding, environmental DNA, and LAMP pathogen testing. "
        "All investigations under this group are public-audience / "
        "citizen-science work, distinct from institutional research groups."
    ),
}


def api(method, path, **kw):
    key = os.environ.get("LIBREBIOTECH_API_KEY")
    if not key:
        sys.exit("error: set LIBREBIOTECH_API_KEY")
    h = kw.pop("headers", {})
    h["X-API-Key"] = key
    h.setdefault("Content-Type", "application/json")
    r = requests.request(method, f"{API_BASE}{path}", headers=h, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--dry-run", action="store_true", help="Print payload; do not POST")
    args = ap.parse_args()

    if args.dry_run:
        print(json.dumps(GROUP, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", "/groups", json=GROUP)
    print(f"HTTP {code}")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
