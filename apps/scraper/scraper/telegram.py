"""Telegram bot notifications for scraper status."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def _api(method: str, **kwargs) -> dict | None:
    if not _TOKEN:
        return None
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{_TOKEN}/{method}",
            json=kwargs,
            timeout=10,
        )
        return r.json()
    except Exception as e:
        logger.warning("Telegram API error: %s", e)
        return None


def send(text: str) -> bool:
    """Send a message to the configured chat. Returns True on success."""
    if not _TOKEN or not _CHAT_ID:
        return False
    result = _api("sendMessage", chat_id=_CHAT_ID, text=text, parse_mode="HTML")
    return bool(result and result.get("ok"))


def notify_store_start(store_name: str, store_id: str) -> bool:
    """Notify that a store scrape has started."""
    return send(f"🔄 <b>{store_name}</b> ({store_id}) — scraping started...")


def notify_store_done(stats: dict) -> bool:
    """Notify that a store scrape has finished."""
    name = stats.get("store", "?")
    err = stats.get("error")
    if err:
        return send(f"❌ <b>{name}</b> — failed: {err[:200]}")

    urls = stats.get("urls", 0)
    new = stats.get("new", 0)
    chg = stats.get("changed", 0)
    rem = stats.get("removed", 0)
    dur = stats.get("duration", "?")
    return send(
        f"✅ <b>{name}</b> — done in {dur}s\n"
        f"   📦 {urls} products | 🆕 {new} new | ✏️ {chg} changed | 🗑 {rem} removed"
    )


def send_summary(results: list[dict], dry_run: bool = False) -> bool:
    """Format and send final scraper summary."""
    if not _TOKEN or not _CHAT_ID:
        return False

    total_urls = sum(r.get("urls", 0) for r in results)
    total_new = sum(r.get("new", 0) for r in results)
    total_changed = sum(r.get("changed", 0) for r in results)
    total_removed = sum(r.get("removed", 0) for r in results)
    errors = [r for r in results if r.get("error")]

    mode = "🧪 DRY RUN" if dry_run else "🚀 LIVE"
    status = "❌" if errors else "✅"

    lines = [f"{status} <b>Scraper {mode} Complete</b> — {len(results)} stores"]
    lines.append("")

    for r in results:
        name = r.get("store", "?")
        err = r.get("error")
        if err:
            lines.append(f"  ❌ {name}")
        else:
            urls = r.get("urls", 0)
            new = r.get("new", 0)
            chg = r.get("changed", 0)
            lines.append(f"  ✅ {name}: {urls} urls, {new} new, {chg} chg")

    lines.append("")
    lines.append(f"📊 <b>Total: {total_urls} products, {total_new} new, {total_changed} changed, {total_removed} removed</b>")
    if errors:
        lines.append(f"⚠️ {len(errors)} store(s) failed")

    return send("\n".join(lines))
