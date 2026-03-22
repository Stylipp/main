"""Interactive Telegram bot for scraper management."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path

import httpx

from .config import StoreConfig, load_stores
from .sitemap import discover_sitemap, fetch_product_urls, SiteBlockedError
from .product_scraper import scrape_product
from .pipeline import run_all

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"

# Persistent stores.yaml path (on volume)
DATA_DIR = Path("/app/data")
STORES_PATH = DATA_DIR / "stores.yaml"
BUNDLED_STORES = Path(__file__).parent.parent / "stores.yaml"


def _ensure_stores_file():
    """Copy bundled stores.yaml to data volume if not exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORES_PATH.exists():
        if BUNDLED_STORES.exists():
            shutil.copy2(BUNDLED_STORES, STORES_PATH)
        else:
            STORES_PATH.write_text("stores:\n")


async def _detect_platform(url: str) -> str:
    """Auto-detect platform by checking homepage HTML for indicators."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            }, follow_redirects=True)
            html = r.text.lower()
            if "shopify" in html or "myshopify.com" in html:
                return "shopify"
            if "magento" in html or "mage-" in html:
                return "magento"
    except Exception:
        pass
    return ""  # default (woocommerce)


async def _send(text: str, parse_mode: str = "HTML") -> None:
    """Send message to configured chat."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{API}/sendMessage", json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": parse_mode,
            })
    except Exception as e:
        logger.warning("Failed to send message: %s", e)


async def _get_updates(offset: int = 0) -> list[dict]:
    """Long poll for new messages."""
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.get(f"{API}/getUpdates", params={
                "offset": offset,
                "timeout": 30,
                "allowed_updates": '["message"]',
            })
            data = r.json()
            return data.get("result", [])
    except Exception as e:
        logger.warning("getUpdates error: %s", e)
        return []


async def cmd_help(**_):
    """Show available commands."""
    await _send(
        "\U0001f916 <b>Stylipp Scraper Bot</b>\n\n"
        "/list \u2014 \u05e8\u05e9\u05d9\u05de\u05ea \u05d7\u05e0\u05d5\u05d9\u05d5\u05ea \u05de\u05d5\u05d2\u05d3\u05e8\u05d5\u05ea\n"
        "/add <code>&lt;url&gt;</code> [platform] \u2014 \u05d4\u05d5\u05e1\u05e4\u05ea \u05d7\u05e0\u05d5\u05ea\n"
        "/remove <code>&lt;store_id&gt;</code> \u2014 \u05d4\u05e1\u05e8\u05ea \u05d7\u05e0\u05d5\u05ea\n"
        "/test <code>&lt;url&gt;</code> \u2014 \u05d1\u05d3\u05d9\u05e7\u05ea \u05d7\u05e0\u05d5\u05ea (sitemap + \u05de\u05d5\u05e6\u05e8 \u05dc\u05d3\u05d5\u05d2\u05de\u05d4)\n"
        "/run [store_id] \u2014 \u05d4\u05e4\u05e2\u05dc\u05ea \u05e1\u05e7\u05e8\u05d9\u05d9\u05e4\n"
        "/status \u2014 \u05e1\u05d8\u05d8\u05d9\u05e1\u05d8\u05d9\u05e7\u05d5\u05ea DB\n"
        "/help \u2014 \u05e2\u05d6\u05e8\u05d4"
    )


async def cmd_list(**_):
    """List all configured stores."""
    stores = load_stores(STORES_PATH)
    if not stores:
        await _send("\U0001f4cb \u05d0\u05d9\u05df \u05d7\u05e0\u05d5\u05d9\u05d5\u05ea \u05de\u05d5\u05d2\u05d3\u05e8\u05d5\u05ea")
        return
    lines = [f"\U0001f4cb <b>{len(stores)} \u05d7\u05e0\u05d5\u05d9\u05d5\u05ea \u05de\u05d5\u05d2\u05d3\u05e8\u05d5\u05ea:</b>\n"]
    for s in stores:
        lines.append(f"  \u2022 <code>{s.id}</code> \u2014 {s.base_url} [{s.platform}]")
    await _send("\n".join(lines))


async def cmd_add(args: str, **_):
    """Add a store to stores.yaml."""
    parts = args.strip().split()
    if not parts:
        await _send(
            "\u274c \u05e9\u05d9\u05de\u05d5\u05e9: /add <code>&lt;url&gt;</code> [platform]\n\n"
            "\u05d3\u05d5\u05d2\u05de\u05d0\u05d5\u05ea:\n"
            "/add https://example.co.il\n"
            "/add https://example.co.il shopify"
        )
        return

    url = parts[0]
    platform = parts[1] if len(parts) > 1 else ""

    # Validate URL
    if not url.startswith("http"):
        url = f"https://{url}"

    # Auto-detect platform if not specified
    if not platform:
        platform = await _detect_platform(url)

    # Check if already exists
    stores = load_stores(STORES_PATH)
    new_store = StoreConfig(url, platform)
    for s in stores:
        if s.id == new_store.id:
            await _send(f"\u26a0\ufe0f \u05d7\u05e0\u05d5\u05ea <code>{new_store.id}</code> \u05db\u05d1\u05e8 \u05e7\u05d9\u05d9\u05de\u05ea")
            return

    # Read current YAML and append
    import yaml
    with open(STORES_PATH) as f:
        data = yaml.safe_load(f) or {}
    store_list = data.get("stores", [])

    if platform:
        store_list.append({"url": url, "platform": platform})
    else:
        store_list.append(url)

    data["stores"] = store_list
    with open(STORES_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    await _send(
        f"\u2705 \u05d7\u05e0\u05d5\u05ea <b>{new_store.name}</b> ({new_store.id}) \u05e0\u05d5\u05e1\u05e4\u05d4\n"
        f"\u05e4\u05dc\u05d8\u05e4\u05d5\u05e8\u05de\u05d4: {new_store.platform}\n"
        f"URL: {url}"
    )


async def cmd_remove(args: str, **_):
    """Remove a store from stores.yaml."""
    store_id = args.strip()
    if not store_id:
        await _send("\u274c \u05e9\u05d9\u05de\u05d5\u05e9: /remove <code>&lt;store_id&gt;</code>")
        return

    import yaml
    with open(STORES_PATH) as f:
        data = yaml.safe_load(f) or {}
    store_list = data.get("stores", [])

    # Find and remove
    new_list = []
    removed = False
    for entry in store_list:
        entry_url = entry if isinstance(entry, str) else entry.get("url", "")
        check = StoreConfig(entry_url)
        if check.id == store_id:
            removed = True
        else:
            new_list.append(entry)

    if not removed:
        await _send(f"\u274c \u05d7\u05e0\u05d5\u05ea <code>{store_id}</code> \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0\u05d4")
        return

    data["stores"] = new_list
    with open(STORES_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    await _send(f"\U0001f5d1 \u05d7\u05e0\u05d5\u05ea <code>{store_id}</code> \u05d4\u05d5\u05e1\u05e8\u05d4")


async def cmd_test(args: str, **_):
    """Test a store -- check sitemap and scrape a sample product."""
    parts = args.strip().split()
    if not parts:
        await _send(
            "\u274c \u05e9\u05d9\u05de\u05d5\u05e9: /test <code>&lt;url&gt;</code> [platform]\n\n"
            "\u05d3\u05d5\u05d2\u05de\u05d0\u05d5\u05ea:\n"
            "/test https://example.co.il\n"
            "/test https://example.co.il magento"
        )
        return

    url = parts[0]
    platform = parts[1] if len(parts) > 1 else ""

    if not url.startswith("http"):
        url = f"https://{url}"

    await _send(f"\U0001f50d \u05d1\u05d5\u05d3\u05e7 \u05d0\u05ea {url}...")

    # Auto-detect platform if not specified
    if not platform:
        platform = await _detect_platform(url)

    store = StoreConfig(url, platform)
    lines = [f"\U0001f50d <b>\u05d1\u05d3\u05d9\u05e7\u05ea {store.name}</b> ({store.platform})\n"]

    # 1. Sitemap discovery
    try:
        sitemap = await discover_sitemap(store.base_url)
    except SiteBlockedError:
        lines.append(
            "\u26d4 <b>\u05d4\u05d0\u05ea\u05e8 \u05d7\u05d5\u05e1\u05dd \u05d0\u05ea \u05d4-IP \u05e9\u05dc \u05d4\u05e9\u05e8\u05ea (403 Forbidden)</b>\n"
            "Cloudflare/WAF \u05de\u05d6\u05d4\u05d4 \u05e9\u05d4\u05d1\u05e7\u05e9\u05d4 \u05de\u05d2\u05d9\u05e2\u05d4 \u05de-datacenter IP \u05d5\u05d7\u05d5\u05e1\u05dd \u05d0\u05d5\u05ea\u05d4.\n\n"
            "\U0001f527 \u05e4\u05ea\u05e8\u05d5\u05e0\u05d5\u05ea \u05d0\u05e4\u05e9\u05e8\u05d9\u05d9\u05dd:\n"
            "  \u2022 \u05e9\u05d9\u05de\u05d5\u05e9 \u05d1-proxy / residential IP\n"
            "  \u2022 \u05d4\u05d5\u05e1\u05e4\u05ea \u05d4-IP \u05dc-whitelist \u05e9\u05dc \u05d4\u05d0\u05ea\u05e8\n"
            "  \u2022 \u05e4\u05e0\u05d9\u05d9\u05d4 \u05dc\u05d1\u05e2\u05dc \u05d4\u05d0\u05ea\u05e8"
        )
        await _send("\n".join(lines))
        return

    if not sitemap:
        lines.append("\u274c \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0 sitemap")
        await _send("\n".join(lines))
        return
    lines.append(f"\u2705 Sitemap: {sitemap}")

    # 2. Fetch product URLs
    store.sitemap_url = sitemap
    product_urls = await fetch_product_urls(store)
    lines.append(f"\U0001f4e6 {len(product_urls)} \u05de\u05d5\u05e6\u05e8\u05d9\u05dd \u05e0\u05de\u05e6\u05d0\u05d5")

    if not product_urls:
        lines.append("\u274c \u05d0\u05d9\u05df \u05de\u05d5\u05e6\u05e8\u05d9\u05dd \u05d1-sitemap")
        await _send("\n".join(lines))
        return

    # 3. Scrape 3 sample products
    lines.append("\n<b>\u05d3\u05d5\u05d2\u05de\u05d0\u05d5\u05ea \u05de\u05d5\u05e6\u05e8\u05d9\u05dd:</b>")
    sample = product_urls[:3]
    success = 0
    for sample_url in sample:
        product = await scrape_product(sample_url, store)
        if product:
            success += 1
            price_str = f"\u20aa{product.price}" if product.price else "N/A"
            imgs = len(product.image_urls)
            lines.append(f"  \u2705 {product.title[:50]} | {price_str} | {imgs} \u05ea\u05de\u05d5\u05e0\u05d5\u05ea")
        else:
            lines.append(f"  \u274c \u05e0\u05db\u05e9\u05dc: {sample_url.split('/')[-1]}")
        await asyncio.sleep(2)  # rate limit

    status_icon = "\u2705" if success > 0 else "\u274c"
    lines.append(
        f"\n{status_icon} "
        f"{success}/{len(sample)} \u05de\u05d5\u05e6\u05e8\u05d9\u05dd \u05e0\u05e1\u05e8\u05e7\u05d5 \u05d1\u05d4\u05e6\u05dc\u05d7\u05d4"
    )
    if success > 0:
        lines.append(
            f"\n\u05dc\u05d4\u05d5\u05e1\u05e4\u05d4: /add {url}"
            + (f" {store.platform}" if store.platform != "woocommerce" else "")
        )

    await _send("\n".join(lines))


async def cmd_run(args: str, **_):
    """Run scraper for all stores or a specific one."""
    store_id = args.strip()
    stores = load_stores(STORES_PATH)

    if store_id:
        match = [s for s in stores if s.id == store_id]
        if not match:
            await _send(f"\u274c \u05d7\u05e0\u05d5\u05ea <code>{store_id}</code> \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0\u05d4")
            return
        stores = match

    count = len(stores)
    names = ", ".join(s.name for s in stores)
    await _send(f"\U0001f680 \u05de\u05ea\u05d7\u05d9\u05dc \u05e1\u05e7\u05e8\u05d9\u05d9\u05e4 \u05dc-{count} \u05d7\u05e0\u05d5\u05d9\u05d5\u05ea: {names}")

    results = await run_all(stores)

    # Send summary (telegram.send_summary is called inside run_all already)
    from . import telegram
    telegram.send_summary(results)


async def cmd_status(**_):
    """Show DB stats."""
    backend_url = os.getenv("BACKEND_API_URL", "")
    if not backend_url:
        await _send("\u274c BACKEND_API_URL \u05dc\u05d0 \u05de\u05d5\u05d2\u05d3\u05e8")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{backend_url}/api/products/count")
            r.raise_for_status()
            count = r.json().get("count", 0)
    except Exception as e:
        await _send(f"\u274c \u05e9\u05d2\u05d9\u05d0\u05d4 \u05d1\u05d7\u05d9\u05d1\u05d5\u05e8 \u05dc\u05d1\u05d0\u05e7\u05e0\u05d3: {e}")
        return

    stores = load_stores(STORES_PATH)
    await _send(
        f"\U0001f4ca <b>\u05e1\u05d8\u05d8\u05d5\u05e1 Stylipp</b>\n\n"
        f"\U0001f5c4 \u05de\u05d5\u05e6\u05e8\u05d9\u05dd \u05d1-DB: <b>{count}</b>\n"
        f"\U0001f3ea \u05d7\u05e0\u05d5\u05d9\u05d5\u05ea \u05de\u05d5\u05d2\u05d3\u05e8\u05d5\u05ea: <b>{len(stores)}</b>"
    )


# Command dispatcher
COMMANDS = {
    "/help": cmd_help,
    "/start": cmd_help,
    "/list": cmd_list,
    "/add": cmd_add,
    "/remove": cmd_remove,
    "/test": cmd_test,
    "/run": cmd_run,
    "/status": cmd_status,
}


async def _handle_message(msg: dict) -> None:
    """Process a single incoming message."""
    text = msg.get("text", "").strip()
    chat_id = msg.get("chat", {}).get("id")

    # Only respond to configured chat
    if str(chat_id) != CHAT_ID:
        return

    if not text.startswith("/"):
        return

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower().split("@")[0]  # handle /command@botname
    args = parts[1] if len(parts) > 1 else ""

    handler = COMMANDS.get(cmd)
    if handler:
        try:
            await handler(args=args)
        except Exception as e:
            logger.error("Command %s failed: %s", cmd, e, exc_info=True)
            await _send(f"\u274c \u05e9\u05d2\u05d9\u05d0\u05d4: {e}")
    else:
        await _send(f"\u2753 \u05e4\u05e7\u05d5\u05d3\u05d4 \u05dc\u05d0 \u05de\u05d5\u05db\u05e8\u05ea: {cmd}\n\u05e0\u05e1\u05d4 /help")


async def run_bot():
    """Main bot loop -- long polling."""
    if not TOKEN or not CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return

    _ensure_stores_file()

    logger.info("Bot started -- listening for commands...")
    await _send("\U0001f916 Bot started! Send /help for commands.")

    offset = 0
    while True:
        updates = await _get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message")
            if msg:
                await _handle_message(msg)
