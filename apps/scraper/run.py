#!/usr/bin/env python3
"""
Product scraper — scrape fashion stores and push to WooCommerce.

Usage:
    python run.py                    # scrape all stores
    python run.py --dry-run          # scrape + diff only, no sync
    python run.py --store mekimi     # specific store
    python run.py --list             # show configured stores
"""

import argparse
import asyncio
import logging
import sys

from scraper.config import load_stores
from scraper.pipeline import run_all, run_store, ChangeDetector, WooSync
from scraper import telegram


def main():
    parser = argparse.ArgumentParser(description="Scrape fashion stores")
    parser.add_argument("--store", help="Run specific store by ID")
    parser.add_argument("--dry-run", action="store_true", help="Scrape + diff only, no WooCommerce sync")
    parser.add_argument("--list", action="store_true", help="List configured stores")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    stores = load_stores()

    if args.list:
        print(f"\n{'ID':<15} {'URL'}")
        print("-" * 50)
        for s in stores:
            print(f"{s.id:<15} {s.base_url}")
        return

    if args.store:
        match = [s for s in stores if s.id == args.store]
        if not match:
            print(f"Store '{args.store}' not found. Available: {', '.join(s.id for s in stores)}")
            sys.exit(1)
        stores = match

    results = asyncio.run(run_all(stores, dry_run=args.dry_run))

    # Print summary
    print(f"\n{'Store':<15} {'URLs':>6} {'New':>5} {'Chg':>5} {'Rem':>5} {'Error'}")
    print("-" * 55)

    has_errors = False
    for r in results:
        err = "YES" if r.get("error") else ""
        if err:
            has_errors = True
        print(
            f"{r.get('store', '?'):<15} "
            f"{r.get('urls', 0):>6} "
            f"{r.get('new', 0):>5} "
            f"{r.get('changed', 0):>5} "
            f"{r.get('removed', 0):>5} "
            f"{err}"
        )

    if args.dry_run:
        print("\n[DRY RUN] No changes synced to WooCommerce")

    # Send Telegram notification
    telegram.send_summary(results, dry_run=args.dry_run)

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
