"""Async product page scraper — JSON-LD first, HTML fallback."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .config import StoreConfig
from .schemas import ScrapedProduct

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def _fetch_with_retry(
    url: str, store: StoreConfig, max_retries: int = 3
) -> httpx.Response:
    """Fetch URL with exponential backoff on 429 responses."""
    for attempt in range(max_retries + 1):
        async with httpx.AsyncClient(timeout=store.timeout_seconds) as client:
            r = await client.get(url, headers=_HEADERS, follow_redirects=True)
            if r.status_code == 429 and attempt < max_retries:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.info(
                    "429 rate limited on %s — waiting %ds (retry %d/%d)",
                    url,
                    wait,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(wait)
                continue
            r.raise_for_status()
            return r
    return r  # unreachable, but keeps type checker happy


async def scrape_product(url: str, store: StoreConfig) -> ScrapedProduct | None:
    """Scrape one product page. Returns None on failure."""
    try:
        r = await _fetch_with_retry(url, store)

        soup = BeautifulSoup(r.text, "html.parser")

        jsonld_data, jsonld_node = _extract_jsonld(soup)
        html_data = _extract_html(soup, store)
        data = _merge_product_data(jsonld_data, html_data)
        if not data or not data.get("title"):
            return None

        stable_id = _extract_stable_id(soup, jsonld_node, store)
        if stable_id:
            prefix = store.platform or "woo"
            external_id = f"{prefix}_{stable_id}"
        else:
            external_id = f"md5_{hashlib.md5(url.encode()).hexdigest()[:16]}"

        return ScrapedProduct(
            url=url,
            external_id=external_id,
            title=data["title"],
            description=data.get("description"),
            price=data.get("price"),
            sale_price=data.get("sale_price"),
            currency=store.currency,
            image_urls=data.get("image_urls", []),
            categories=data.get("categories", []),
            store_id=store.id,
            scraped_at=datetime.utcnow(),
        )
    except Exception:
        logger.warning("Failed to scrape %s", url, exc_info=True)
        return None


async def scrape_batch(urls: list[str], store: StoreConfig) -> list[ScrapedProduct]:
    """Scrape multiple URLs with rate limiting."""
    results = []
    for i, url in enumerate(urls, 1):
        product = await scrape_product(url, store)
        if product:
            results.append(product)
        if i % 50 == 0 or i == len(urls):
            logger.info(
                "%d/%d scraped for %s (%d ok)", i, len(urls), store.name, len(results)
            )
        if i < len(urls):
            await asyncio.sleep(store.rate_limit_seconds)
    return results


# --- Stable ID extraction ---


def _extract_stable_id(
    soup: BeautifulSoup, jsonld_node: dict | None, store: StoreConfig
) -> str | None:
    """Extract a platform-native product ID, falling back to None for md5."""
    # 1. JSON-LD sku (cross-platform, highest reliability)
    if jsonld_node:
        sku = str(jsonld_node.get("sku", "")).strip()
        if sku:
            return sku

    # 2. WooCommerce data-product_id HTML attribute
    el = soup.find(attrs={"data-product_id": True})
    if el:
        pid = str(el.get("data-product_id", "")).strip()
        if pid:
            return pid

    # 3. Shopify productGroupID from JSON-LD
    if jsonld_node:
        group_id = str(jsonld_node.get("productGroupID", "")).strip()
        if group_id:
            return group_id

    return None


# --- JSON-LD extraction ---


def _extract_jsonld(
    soup: BeautifulSoup,
) -> tuple[dict[str, Any] | None, dict | None]:
    """Return (merged product data, raw JSON-LD node) from structured data."""
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue

        node = _find_product_node(data)
        if node:
            title = _norm(str(node.get("name", "")))
            if not title:
                continue

            desc = _norm(str(node.get("description", "")))[:1000] or None
            images = _extract_images(node)
            price, sale_price = _extract_price(node)

            return {
                "title": title,
                "description": desc,
                "price": price,
                "sale_price": sale_price,
                "image_urls": images,
                "categories": [],
            }, node
    return None, None


def _merge_product_data(
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Prefer structured data, but keep taxonomy and missing fields from HTML."""
    if primary is None:
        return secondary
    if secondary is None:
        return primary

    return {
        "title": primary.get("title") or secondary.get("title"),
        "description": primary.get("description") or secondary.get("description"),
        "price": (
            primary.get("price")
            if primary.get("price") is not None
            else secondary.get("price")
        ),
        "sale_price": (
            primary.get("sale_price")
            if primary.get("sale_price") is not None
            else secondary.get("sale_price")
        ),
        "image_urls": list(
            dict.fromkeys(
                [
                    *(primary.get("image_urls") or []),
                    *(secondary.get("image_urls") or []),
                ]
            )
        ),
        "categories": list(
            dict.fromkeys(
                [
                    *(primary.get("categories") or []),
                    *(secondary.get("categories") or []),
                ]
            )
        ),
    }


def _find_product_node(data: Any) -> dict | None:
    if isinstance(data, dict):
        items = data.get("@graph", [data])
        if isinstance(items, dict):
            items = [items]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type", "")
            if t == "Product" or (isinstance(t, list) and "Product" in t):
                return item
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("@type") == "Product":
                return item
    return None


def _extract_images(node: dict) -> list[str]:
    img = node.get("image")
    urls: list[str] = []
    if isinstance(img, str):
        urls.append(img)
    elif isinstance(img, list):
        for i in img:
            if isinstance(i, str):
                urls.append(i)
            elif isinstance(i, dict):
                u = i.get("url") or i.get("contentUrl") or i.get("@id")
                if u:
                    urls.append(u)
    elif isinstance(img, dict):
        u = img.get("url") or img.get("contentUrl") or img.get("@id")
        if u:
            urls.append(u)
    return list(dict.fromkeys(urls))  # dedupe, preserve order


def _extract_price(node: dict) -> tuple[Decimal | None, Decimal | None]:
    offers = node.get("offers")
    if not offers:
        return None, None
    offer = (
        offers
        if isinstance(offers, dict)
        else (offers[0] if isinstance(offers, list) and offers else None)
    )
    if not offer or not isinstance(offer, dict):
        return None, None
    return _parse_price(offer.get("price")), None


# --- HTML fallback ---


def _extract_html(soup: BeautifulSoup, store: StoreConfig) -> dict[str, Any]:
    sel = store.selectors

    title_el = soup.select_one(sel["title"])
    title = _text(title_el) if title_el else ""

    price, sale_price = None, None
    reg = soup.select_one(sel["price_regular"])
    if reg:
        price = _parse_price(_text(reg))
    sale = soup.select_one(sel["price_sale"])
    if sale:
        sale_price = _parse_price(_text(sale))
    if price is None and sale_price is None:
        single = soup.select_one(sel["price_single"])
        if single:
            price = _parse_price(_text(single))

    desc_el = soup.select_one(sel["description"])
    desc = _text(desc_el)[:1000] if desc_el else None

    skip = {"home", "בית", "דף הבית"}
    cats = [
        _text(a) for a in soup.select(sel["categories"]) if _text(a).lower() not in skip
    ]

    images = []
    for img in soup.select(sel["images"]):
        src = img.get("data-large_image") or img.get("data-src") or img.get("src")
        if src and "placeholder" not in src:
            images.append(src)
    images = list(dict.fromkeys(images))

    return {
        "title": title,
        "description": desc,
        "price": price,
        "sale_price": sale_price,
        "image_urls": images,
        "categories": cats,
    }


# --- helpers ---


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip() if text else ""


def _text(el: Any) -> str:
    return _norm(el.get_text(" ", strip=True)) if el else ""


def _parse_price(text: Any) -> Decimal | None:
    if not text:
        return None
    text = re.sub(r"[^\d.,]", "", str(text))
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    m = re.search(r"\d+(\.\d+)?", text)
    if not m:
        return None
    try:
        return Decimal(m.group(0))
    except InvalidOperation:
        return None
