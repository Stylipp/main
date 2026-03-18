"""Async sitemap fetcher — auto-discovers and parses sitemaps."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from .config import SITEMAP_CANDIDATES, StoreConfig

logger = logging.getLogger(__name__)

_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


async def _fetch_xml(url: str, timeout: float = 30.0) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, headers={"User-Agent": _UA})
            r.raise_for_status()
            return r.text
    except Exception:
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
            loc = el.find(f"{_NS}loc") or el.find("loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
        if urls:
            break
    return urls


async def discover_sitemap(base_url: str) -> str | None:
    """Try common sitemap paths, return first that works."""
    for path in SITEMAP_CANDIDATES:
        url = f"{base_url}{path}"
        if await _fetch_xml(url) is not None:
            logger.info("Discovered sitemap: %s", url)
            return url
    logger.warning("No sitemap found for %s", base_url)
    return None


async def fetch_product_urls(store: StoreConfig) -> list[str]:
    """Fetch all product URLs from a store's sitemap."""
    sitemap_url = store.sitemap_url
    if not sitemap_url:
        sitemap_url = await discover_sitemap(store.base_url)
        if not sitemap_url:
            return []
        store.sitemap_url = sitemap_url

    xml = await _fetch_xml(sitemap_url)
    if xml is None:
        return []

    urls = _parse_urls(xml)

    # Handle sitemap index (contains sub-sitemaps instead of URLs)
    if not urls:
        subs = _parse_sub_sitemaps(xml)
        if subs:
            logger.info("Sitemap index with %d sub-sitemaps for %s", len(subs), store.name)
            for sub_url in subs:
                sub_xml = await _fetch_xml(sub_url)
                if sub_xml:
                    urls.extend(_parse_urls(sub_xml))

    product_urls = sorted(set(u for u in urls if store.product_url_pattern in u))
    logger.info("%s: %d total URLs, %d product URLs", store.name, len(urls), len(product_urls))
    return product_urls
