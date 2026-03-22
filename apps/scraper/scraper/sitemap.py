"""Async sitemap fetcher — auto-discovers and parses sitemaps."""

from __future__ import annotations

import asyncio
import logging
import re
import xml.etree.ElementTree as ET

import httpx

from .config import SITEMAP_CANDIDATES, StoreConfig

logger = logging.getLogger(__name__)


class SiteBlockedError(Exception):
    """Raised when a site returns 403 — likely Cloudflare/WAF IP block."""

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"403 Forbidden — site blocks this IP: {url}")

_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


async def _fetch_xml(url: str, timeout: float = 30.0, max_retries: int = 3) -> str | None:
    """Fetch XML from *url*. Returns text on success, None on 404/other errors.

    Raises ``SiteBlockedError`` on HTTP 403 (Cloudflare / WAF block).
    """
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(url, headers=_HEADERS)
                if r.status_code == 429 and attempt < max_retries:
                    wait = 2 ** (attempt + 1)
                    logger.info("429 on sitemap %s — waiting %ds (retry %d/%d)", url, wait, attempt + 1, max_retries)
                    await asyncio.sleep(wait)
                    continue
                if r.status_code == 403:
                    raise SiteBlockedError(url)
                r.raise_for_status()
                return r.text
        except SiteBlockedError:
            raise
        except httpx.HTTPStatusError:
            return None
        except Exception:
            return None
    return None


def _parse_urls(xml_text: str) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    urls = [el.text.strip() for el in root.iter(f"{_NS}loc") if el.text]
    if not urls:
        urls = [el.text.strip() for el in root.iter("loc") if el.text]
    return urls


def _parse_sub_sitemaps(xml_text: str) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    urls = []
    for tag in [f"{_NS}sitemap", "sitemap"]:
        for el in root.iter(tag):
            loc = el.find(f"{_NS}loc")
            if loc is None:
                loc = el.find("loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
        if urls:
            break
    return urls


async def discover_sitemap(base_url: str) -> str | None:
    """Try common sitemap paths, return first that works.

    Raises ``SiteBlockedError`` when the site returns 403 (Cloudflare block).
    """
    for i, path in enumerate(SITEMAP_CANDIDATES):
        if i > 0:
            await asyncio.sleep(1)  # avoid rate limits during discovery
        url = f"{base_url}{path}"
        try:
            if await _fetch_xml(url) is not None:
                logger.info("Discovered sitemap: %s", url)
                return url
        except SiteBlockedError:
            logger.error(
                "⛔ %s returned 403 Forbidden — Cloudflare/WAF is blocking this server's IP. "
                "The site cannot be scraped without a proxy.",
                base_url,
            )
            raise
    logger.warning("No sitemap found for %s", base_url)
    return None


async def fetch_product_urls(store: StoreConfig) -> list[str]:
    """Fetch all product URLs from a store's sitemap.

    Returns empty list on failure.  Raises ``SiteBlockedError`` when 403'd.
    """
    sitemap_url = store.sitemap_url
    if not sitemap_url:
        sitemap_url = await discover_sitemap(store.base_url)  # may raise SiteBlockedError
        if not sitemap_url:
            return []
        store.sitemap_url = sitemap_url

    xml = await _fetch_xml(sitemap_url)
    if xml is None:
        return []

    # Check for sitemap index first (contains sub-sitemaps)
    subs = _parse_sub_sitemaps(xml)
    if subs:
        logger.info("Sitemap index with %d sub-sitemaps for %s", len(subs), store.name)
        # Prefer product-specific sub-sitemaps if available
        product_subs = [s for s in subs if "product" in s.lower()]
        target_subs = product_subs if product_subs else subs
        urls = []
        for sub_url in target_subs:
            sub_xml = await _fetch_xml(sub_url)
            if sub_xml:
                urls.extend(_parse_urls(sub_xml))
    else:
        urls = _parse_urls(xml)

    # If the sitemap itself is product-specific, trust all URLs
    is_product_sitemap = any(
        kw in sitemap_url.lower() for kw in ("product", "products")
    )

    if is_product_sitemap:
        # All URLs in a product-specific sitemap are products — skip filtering
        product_urls = sorted(set(u for u in urls if u.rstrip("/") != store.base_url.rstrip("/")))
    elif store.product_url_regex:
        pat = re.compile(store.product_url_regex)
        product_urls = sorted(set(u for u in urls if pat.search(u)))
    elif store.product_url_pattern:
        product_urls = sorted(set(u for u in urls if store.product_url_pattern in u))
    else:
        product_urls = sorted(set(urls))

    logger.info("%s: %d total URLs, %d product URLs", store.name, len(urls), len(product_urls))
    return product_urls
