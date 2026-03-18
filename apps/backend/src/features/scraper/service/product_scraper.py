"""Async product page scraper with JSON-LD and HTML fallback extraction.

Ports The Sprapper's extraction logic to async httpx with configurable
CSS selectors per store. Produces ScrapedProduct objects for the pipeline.
"""

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

from src.features.scraper.config.stores import StoreConfig
from src.features.scraper.schemas.schemas import ScrapedProduct

logger = logging.getLogger(__name__)

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class ProductScraper:
    """Scrapes individual product pages using JSON-LD + HTML fallback."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def scrape_product(
        self, url: str, store: StoreConfig
    ) -> ScrapedProduct | None:
        """Scrape a single product page and return a ScrapedProduct.

        Fetches the page HTML, tries JSON-LD extraction first, then falls
        back to HTML CSS selectors. Returns None on any error so the
        pipeline can continue with the next product.
        """
        try:
            html = await self._fetch_page(url, store.timeout_seconds)
            if html is None:
                return None

            soup = BeautifulSoup(html, "html.parser")

            # Try JSON-LD extraction first
            data = self._extract_from_jsonld(soup, url)

            # Fall back to HTML selectors
            if data is None:
                data = self._extract_from_html(soup, store)

            if not data or not data.get("title"):
                logger.warning("No product data extracted from %s", url)
                return None

            external_id = hashlib.md5(url.encode()).hexdigest()[:16]

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
            logger.warning("Error scraping product %s", url, exc_info=True)
            return None

    async def scrape_batch(
        self, urls: list[str], store: StoreConfig
    ) -> list[ScrapedProduct]:
        """Scrape multiple URLs sequentially with rate limiting.

        Sleeps store.rate_limit_seconds between requests to be polite.
        Logs progress every 50 products.
        Returns only successfully scraped products (non-None).
        """
        results: list[ScrapedProduct] = []
        total = len(urls)

        for i, url in enumerate(urls, 1):
            product = await self.scrape_product(url, store)
            if product is not None:
                results.append(product)

            if i % 50 == 0 or i == total:
                logger.info(
                    "%d/%d products scraped for %s",
                    len(results),
                    total,
                    store.name,
                )

            # Rate limit between requests (skip after last)
            if i < total:
                await asyncio.sleep(store.rate_limit_seconds)

        return results

    # ------------------------------------------------------------------
    # JSON-LD extraction (ported from The Sprapper)
    # ------------------------------------------------------------------

    def _extract_from_jsonld(
        self, soup: BeautifulSoup, url: str
    ) -> dict[str, Any] | None:
        """Extract product data from JSON-LD script tags.

        Supports:
        - Yoast SEO @graph arrays containing a Product node
        - Direct Product JSON-LD objects
        - Top-level list of JSON-LD objects
        """
        product_node = self._find_product_jsonld(soup)
        if product_node is None:
            return None

        title = _normalize(str(product_node.get("name", "")))
        if not title:
            return None

        description = _normalize(str(product_node.get("description", "")))
        if description:
            description = description[:1000]

        # Extract images
        image_urls = self._extract_jsonld_images(product_node)

        # Extract price from offers
        price, sale_price = self._extract_jsonld_prices(product_node)

        return {
            "title": title,
            "description": description or None,
            "price": price,
            "sale_price": sale_price,
            "image_urls": image_urls,
            "categories": [],
        }

    @staticmethod
    def _find_product_jsonld(soup: BeautifulSoup) -> dict[str, Any] | None:
        """Find a Product node in all JSON-LD blocks on the page."""
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            raw = script.string or script.get_text() or ""
            raw = raw.strip()
            if not raw:
                continue

            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue

            if isinstance(data, dict):
                # Check @graph array (Yoast SEO pattern)
                items = data.get("@graph", [data])
                if isinstance(items, dict):
                    items = [items]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("@type", "")
                    if item_type == "Product" or (
                        isinstance(item_type, list) and "Product" in item_type
                    ):
                        return item

            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item

        return None

    @staticmethod
    def _extract_jsonld_images(product_node: dict[str, Any]) -> list[str]:
        """Extract image URLs from a JSON-LD Product node."""
        images: list[str] = []
        img_data = product_node.get("image")

        if isinstance(img_data, str):
            images.append(img_data)
        elif isinstance(img_data, list):
            for img in img_data:
                if isinstance(img, str):
                    images.append(img)
                elif isinstance(img, dict):
                    img_url = img.get("url") or img.get("contentUrl") or img.get("@id")
                    if img_url and isinstance(img_url, str):
                        images.append(img_url)
        elif isinstance(img_data, dict):
            img_url = (
                img_data.get("url") or img_data.get("contentUrl") or img_data.get("@id")
            )
            if img_url and isinstance(img_url, str):
                images.append(img_url)

        # Deduplicate preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for url in images:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return unique

    @staticmethod
    def _extract_jsonld_prices(
        product_node: dict[str, Any],
    ) -> tuple[Decimal | None, Decimal | None]:
        """Extract price from JSON-LD offers. Returns (price, sale_price)."""
        offers = product_node.get("offers")
        if offers is None:
            return None, None

        # Normalize to single offer dict
        offer: dict[str, Any] | None = None
        if isinstance(offers, dict):
            offer = offers
        elif isinstance(offers, list) and offers:
            offer = offers[0] if isinstance(offers[0], dict) else None

        if offer is None:
            return None, None

        price = _parse_price(offer.get("price"))
        # JSON-LD typically only has one price; no separate sale_price
        return price, None

    # ------------------------------------------------------------------
    # HTML fallback extraction (ported from The Sprapper)
    # ------------------------------------------------------------------

    def _extract_from_html(
        self, soup: BeautifulSoup, store: StoreConfig
    ) -> dict[str, Any]:
        """Extract product data using store-specific CSS selectors."""
        selectors = store.selectors

        # Title
        title_el = soup.select_one(selectors.title)
        title = _safe_text(title_el) if title_el else ""

        # Prices
        price, sale_price = self._extract_html_prices(soup, store)

        # Description
        desc_el = soup.select_one(selectors.description)
        description = _safe_text(desc_el)[:1000] if desc_el else None

        # Categories — skip "Home"/"daf habayit" entries
        skip_cats = {"home", "בית", "דף הבית"}
        categories: list[str] = []
        for a_tag in soup.select(selectors.categories):
            text = _safe_text(a_tag)
            if text and text.lower() not in skip_cats:
                categories.append(text)

        # Images
        image_urls = self._extract_html_images(soup, store)

        return {
            "title": title,
            "description": description,
            "price": price,
            "sale_price": sale_price,
            "image_urls": image_urls,
            "categories": categories,
        }

    @staticmethod
    def _extract_html_prices(
        soup: BeautifulSoup, store: StoreConfig
    ) -> tuple[Decimal | None, Decimal | None]:
        """Extract prices from HTML using store CSS selectors.

        Logic ported from The Sprapper:
        - price_regular: crossed-out / original price (del element)
        - price_sale: discounted price (ins element)
        - price_single: fallback single price when no sale
        """
        selectors = store.selectors
        price: Decimal | None = None
        sale_price: Decimal | None = None

        # Try regular (crossed-out) price
        regular_el = soup.select_one(selectors.price_regular)
        if regular_el:
            price = _parse_price(_safe_text(regular_el))

        # Try sale price
        sale_el = soup.select_one(selectors.price_sale)
        if sale_el:
            sale_price = _parse_price(_safe_text(sale_el))

        # Fallback: single price (no sale)
        if price is None and sale_price is None:
            single_el = soup.select_one(selectors.price_single)
            if single_el:
                price = _parse_price(_safe_text(single_el))

        return price, sale_price

    @staticmethod
    def _extract_html_images(soup: BeautifulSoup, store: StoreConfig) -> list[str]:
        """Extract product images using store CSS selectors.

        For WooCommerce, prefers data-large_image attribute over src.
        Deduplicates while preserving order.
        """
        images: list[str] = []

        for img in soup.select(store.selectors.images):
            # WooCommerce pattern: prefer large image data attribute
            src = img.get("data-large_image") or img.get("data-src") or img.get("src")
            if src and not src.endswith("placeholder.png"):
                images.append(src)

        # Deduplicate preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for url in images:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return unique

    # ------------------------------------------------------------------
    # Network helper
    # ------------------------------------------------------------------

    async def _fetch_page(self, url: str, timeout: float | None = None) -> str | None:
        """Fetch a page's HTML. Returns None on failure."""
        effective_timeout = timeout or self.timeout
        try:
            async with httpx.AsyncClient(timeout=effective_timeout) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": _USER_AGENT},
                    follow_redirects=True,
                )
                response.raise_for_status()
                return response.text

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HTTP %d fetching %s",
                exc.response.status_code,
                url,
            )
            return None

        except httpx.TimeoutException:
            logger.warning("Timeout fetching %s", url)
            return None

        except Exception:
            logger.warning("Error fetching %s", url, exc_info=True)
            return None


# ------------------------------------------------------------------
# Module-level helpers (ported from The Sprapper)
# ------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Normalize whitespace in text."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _safe_text(el: Any) -> str:
    """Safely get text from a BeautifulSoup element."""
    if el is None:
        return ""
    return _normalize(el.get_text(" ", strip=True))


def _parse_price(text: Any) -> Decimal | None:
    """Parse a price string to Decimal, stripping currency symbols.

    Handles formats like '₪99.90', '$1,299.00', '1.299,00' (European).
    Returns None if parsing fails.
    """
    if not text:
        return None
    text = str(text)

    # Remove currency symbols and whitespace
    text = re.sub(r"[^\d.,]", "", text)

    if not text:
        return None

    # Handle mixed separators: 1,299.00 → remove commas
    if "," in text and "." in text:
        text = text.replace(",", "")
    # Handle comma-only as decimal (European): 99,90 → 99.90
    elif "," in text:
        text = text.replace(",", ".")

    # Extract first valid number
    match = re.search(r"\d+(\.\d+)?", text)
    if not match:
        return None

    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None
