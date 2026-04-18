#!/usr/bin/env python3
"""
Create the Sushi Truth Investigation on LibreBiotech via the REST API.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python create_investigation.py --dry-run        # show payload + chosen group
    python create_investigation.py                  # POST /investigations
    python create_investigation.py --group-id 7     # override auto-selection

group_id is required by the API. The script auto-picks the first group where
you are Leader or Manager (via GET /me/groups). Override with --group-id.

API reference: https://librebiotech.org/?action=docs&page=api#investigations
"""

import argparse
import json
import os
import sys

import requests

API_BASE = "https://librebiotech.org/api.php/v1"

INVESTIGATION = {
    "title": "Sushi Truth: Consumer Fish Mislabeling",
    "description": (
        "Open citizen-science investigation into mislabeling of retail fish "
        "products (sushi, sashimi, fillets) using DNA barcoding of the "
        "mitochondrial COI region. Samples collected by community "
        "participants; analysis follows the garage-genomics "
        "coi-fish-barcoding protocol "
        "(https://github.com/kjdudley/garage-genomics). Results aggregate "
        "into a public dataset of mislabeling observations by vendor, city, "
        "and product type."
    ),
    "status": "Active",
    "visibility": "group",          # flip to "public" via PUT once seeded
    "license": "CC-BY-4.0",
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


def unwrap_groups(body):
    """Tolerate a few plausible response shapes for /me/groups."""
    data = body.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("groups", "memberships", "items"):
            v = data.get(key)
            if isinstance(v, list):
                return v
    return []


def pick_group():
    code, body = api("GET", "/me/groups")
    if code != 200 or not body.get("success"):
        sys.exit(f"groups lookup failed: HTTP {code}\n{json.dumps(body, indent=2)}")
    groups = unwrap_groups(body)
    if not groups:
        sys.exit("no groups found on this account. Create one in the LibreBiotech UI first.")
    for g in groups:
        role = str(g.get("role", "")).lower()
        if role in ("leader", "manager"):
            return g
    sys.exit(
        "no group where you are Leader or Manager. Groups visible to you:\n"
        + json.dumps(groups, indent=2)
    )


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true", help="Print payload; do not POST")
    ap.add_argument("--group-id", type=int, help="Override group_id selection")
    args = ap.parse_args()

    if args.group_id is not None:
        gid = args.group_id
        print(f"Using supplied group_id={gid}", file=sys.stderr)
    else:
        g = pick_group()
        gid = g["id"]
        print(
            f"Using group id={gid} "
            f"(name={g.get('name','?')!r}, role={g.get('role','?')!r})",
            file=sys.stderr,
        )

    payload = {**INVESTIGATION, "group_id": gid}

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", "/investigations", json=payload)
    print(f"HTTP {code}")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
