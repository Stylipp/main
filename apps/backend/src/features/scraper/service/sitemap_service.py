"""Async sitemap fetcher and product URL extractor.

Fetches XML sitemaps from configured store URLs, parses them to extract
product page URLs, and handles sitemap index files (sub-sitemaps).
"""

import logging
import xml.etree.ElementTree as ET

import httpx

from src.features.scraper.config.stores import SITEMAP_CANDIDATES, StoreConfig

logger = logging.getLogger(__name__)

# Standard sitemap XML namespace
_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class SitemapService:
    """Fetches and parses XML sitemaps to extract product URLs."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def discover_sitemap_url(self, base_url: str) -> str | None:
        """Try common sitemap paths and return the first one that works."""
        for candidate in SITEMAP_CANDIDATES:
            url = f"{base_url.rstrip('/')}{candidate}"
            xml_text = await self._fetch_xml(url)
            if xml_text is not None:
                logger.info("Discovered sitemap: %s", url)
                return url
        logger.warning("No sitemap found for %s", base_url)
        return None

    async def fetch_product_urls(self, store: StoreConfig) -> list[str]:
        """Fetch sitemap XML and extract product URLs for a store.

        1. If store.sitemap_url is empty, auto-discovers by trying common paths.
        2. Fetches the sitemap XML.
        3. If the response is a sitemap index, recursively fetches sub-sitemaps.
        4. Filters URLs to those matching store.product_url_pattern.
        5. Returns a sorted, deduplicated list.

        On any network or parse error, logs a warning and returns an empty list
        so the pipeline can continue with other stores.
        """
        try:
            # Auto-discover sitemap if not configured
            sitemap_url = store.sitemap_url
            if not sitemap_url:
                sitemap_url = await self.discover_sitemap_url(store.base_url)
                if not sitemap_url:
                    return []
                # Cache the discovered URL on the store config
                store.sitemap_url = sitemap_url

            xml_text = await self._fetch_xml(sitemap_url)
            if xml_text is None:
                return []

            all_urls = self._parse_urls(xml_text)

            # Check if this is a sitemap index (contains <sitemapindex>)
            if not all_urls:
                sub_sitemap_urls = self._parse_sitemap_index(xml_text)
                if sub_sitemap_urls:
                    logger.info(
                        "Sitemap index detected for %s with %d sub-sitemaps",
                        store.name,
                        len(sub_sitemap_urls),
                    )
                    all_urls = await self.fetch_sitemap_index(
                        store.sitemap_url, sub_sitemap_urls
                    )

            # Filter to product URLs only
            product_urls = [url for url in all_urls if store.product_url_pattern in url]

            # Deduplicate and sort
            product_urls = sorted(set(product_urls))

            logger.info(
                "Store %s: %d total URLs found, %d product URLs after filtering",
                store.name,
                len(all_urls),
                len(product_urls),
            )

            return product_urls

        except Exception:
            logger.warning(
                "Unexpected error fetching sitemap for %s",
                store.name,
                exc_info=True,
            )
            return []

    async def fetch_sitemap_index(
        self, index_url: str, sub_urls: list[str] | None = None
    ) -> list[str]:
        """Handle sitemap index files containing sub-sitemap references.

        If sub_urls is not provided, fetches and parses the index_url first
        to discover sub-sitemap locations. Then fetches each sub-sitemap
        and aggregates all <loc> URLs.

        Returns a flat list of all page URLs found across sub-sitemaps.
        """
        if sub_urls is None:
            xml_text = await self._fetch_xml(index_url)
            if xml_text is None:
                return []
            sub_urls = self._parse_sitemap_index(xml_text)

        all_urls: list[str] = []
        for sub_url in sub_urls:
            xml_text = await self._fetch_xml(sub_url)
            if xml_text is None:
                continue
            urls = self._parse_urls(xml_text)
            all_urls.extend(urls)

        return all_urls

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_xml(self, url: str) -> str | None:
        """Fetch XML content from a URL. Returns None on failure."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": _USER_AGENT},
                )
                response.raise_for_status()
                return response.text

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HTTP %d fetching sitemap %s",
                exc.response.status_code,
                url,
            )
            return None

        except httpx.TimeoutException:
            logger.warning("Timeout fetching sitemap %s", url)
            return None

        except Exception:
            logger.warning("Error fetching sitemap %s", url, exc_info=True)
            return None

    @staticmethod
    def _parse_urls(xml_text: str) -> list[str]:
        """Parse <url><loc> entries from a sitemap XML string."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Failed to parse sitemap XML")
            return []

        urls: list[str] = []
        # Handle both namespaced and non-namespaced tags
        for url_el in root.iter(f"{_SITEMAP_NS}url"):
            loc_el = url_el.find(f"{_SITEMAP_NS}loc")
            if loc_el is not None and loc_el.text:
                urls.append(loc_el.text.strip())

        # Fallback: try without namespace (some sitemaps omit it)
        if not urls:
            for url_el in root.iter("url"):
                loc_el = url_el.find("loc")
                if loc_el is not None and loc_el.text:
                    urls.append(loc_el.text.strip())

        return urls

    @staticmethod
    def _parse_sitemap_index(xml_text: str) -> list[str]:
        """Parse <sitemapindex><sitemap><loc> entries to find sub-sitemaps."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Failed to parse sitemap index XML")
            return []

        sub_urls: list[str] = []

        # Namespaced
        for sitemap_el in root.iter(f"{_SITEMAP_NS}sitemap"):
            loc_el = sitemap_el.find(f"{_SITEMAP_NS}loc")
            if loc_el is not None and loc_el.text:
                sub_urls.append(loc_el.text.strip())

        # Fallback: non-namespaced
        if not sub_urls:
            for sitemap_el in root.iter("sitemap"):
                loc_el = sitemap_el.find("loc")
                if loc_el is not None and loc_el.text:
                    sub_urls.append(loc_el.text.strip())

        return sub_urls
