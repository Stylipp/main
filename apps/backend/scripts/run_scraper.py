"""Automated product scraper -- nightly pipeline runner.

Usage:
    python -m scripts.run_scraper              # Run all enabled stores
    python -m scripts.run_scraper --store mekimi  # Run specific store only
    python -m scripts.run_scraper --dry-run     # Scrape and diff only, no sync
    python -m scripts.run_scraper --list-stores # Show configured stores
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from src.core.config import get_settings
from src.features.scraper.config.stores import load_store_configs
from src.features.scraper.schemas.schemas import PipelineResult
from src.features.scraper.service.orchestrator import ScraperOrchestrator

logger = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Automated product scraper pipeline runner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--store",
        type=str,
        default=None,
        help="Run only this specific store (by store config id).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Scrape and detect changes but don't sync to any system.",
    )
    parser.add_argument(
        "--list-stores",
        action="store_true",
        default=False,
        help="Print configured stores and exit.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable DEBUG logging.",
    )
    return parser.parse_args(argv)


def _configure_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _print_store_table() -> None:
    """Print a table of configured stores and exit."""
    config = load_store_configs()
    header = f"{'ID':<15} {'Name':<20} {'Enabled':<10} {'Sitemap URL'}"
    print()
    print(header)
    print("-" * len(header) + "-" * 30)
    for store in config.stores:
        enabled = "yes" if store.enabled else "no"
        print(f"{store.id:<15} {store.name:<20} {enabled:<10} {store.sitemap_url}")
    print()
    print(f"Total: {len(config.stores)} stores ({len(config.get_enabled_stores())} enabled)")
    print()


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"


def _print_results(result: PipelineResult) -> None:
    """Print a formatted summary table of pipeline results."""
    duration = (result.finished_at - result.started_at).total_seconds()

    # Calculate column widths
    stores = result.stores
    if not stores:
        print("\nNo stores processed.")
        return

    print()
    print("+----------------------------------------------------------+")
    print("|            Scraper Pipeline Results                       |")
    print("+---------------+-------+-----+---------+---------+---------+")
    print("| Store         | URLs  | New | Changed | Removed | Errors  |")
    print("+---------------+-------+-----+---------+---------+---------+")

    for sr in stores:
        error_mark = "YES" if sr.errors else "-"
        print(
            f"| {sr.store_id:<13} "
            f"| {sr.total_urls:>5} "
            f"| {sr.total_new:>3} "
            f"| {sr.total_changed:>7} "
            f"| {sr.total_removed:>7} "
            f"| {error_mark:<7} |"
        )

    print("+---------------+-------+-----+---------+---------+---------+")

    # Sync results
    if result.sync:
        print("|  Sync: ", end="")
        total_db_created = sum(s.db_created for s in result.sync)
        total_db_updated = sum(s.db_updated for s in result.sync)
        total_qdrant = sum(s.qdrant_upserted for s in result.sync)
        print(
            f"DB +{total_db_created} ~{total_db_updated} | "
            f"Qdrant {total_qdrant} vectors"
            + " " * 10
            + "|"
        )
        print("+----------------------------------------------------------+")

    # Re-cluster status
    total_new = sum(r.total_new for r in stores)
    total_changed = sum(r.total_changed for r in stores)
    recluster_label = "Yes" if result.recluster_triggered else "No"
    print(
        f"|  Re-cluster: {recluster_label} "
        f"({total_new + total_changed} changed)"
        + " " * max(0, 35 - len(str(total_new + total_changed)) - len(recluster_label))
        + "|"
    )

    # Duration
    formatted_duration = _format_duration(duration)
    print(
        f"|  Duration: {formatted_duration}"
        + " " * max(0, 47 - len(formatted_duration))
        + "|"
    )
    print("+----------------------------------------------------------+")
    print()


async def main(argv: list[str] | None = None) -> int:
    """Run the scraper pipeline.

    Args:
        argv: Command-line arguments (defaults to sys.argv).

    Returns:
        Exit code: 0 on success, 1 on any store failure.
    """
    args = _parse_args(argv)
    _configure_logging(args.verbose)

    settings = get_settings()

    # --list-stores: print and exit
    if args.list_stores:
        _print_store_table()
        return 0

    # Determine which stores to run
    stores = None
    if args.store:
        config = load_store_configs()
        matching = [s for s in config.stores if s.id == args.store]
        if not matching:
            print(f"Error: Store '{args.store}' not found in configuration.")
            print("Available stores:", ", ".join(s.id for s in config.stores))
            return 1
        stores = matching
        # Force-enable the store when explicitly requested
        for s in stores:
            s.enabled = True

    # Run pipeline
    if args.dry_run:
        logger.info("[DRY RUN] Scraping and detecting changes only, no sync")

    orchestrator = ScraperOrchestrator(settings)
    result = await orchestrator.run_all(stores=stores, dry_run=args.dry_run)

    # Print results
    _print_results(result)

    # Exit code
    has_errors = any(sr.errors for sr in result.stores)
    return 1 if has_errors else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
