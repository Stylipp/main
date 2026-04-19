#!/usr/bin/env python3
"""
WooCommerce Product Scraper - Full Export Format
Scrapes products including variations and all attributes, matching WordPress export format.
"""

import os
import re
import csv
import json
import time
import hashlib
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional, Tuple
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================

INPUT_XML = "input/products.xml"
OUTPUT_CSV = "output/products_full.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

TIMEOUT = 30
SLEEP_SEC = 0.35

# Maximum number of attributes to support
MAX_ATTRIBUTES = 5


# =========================
# WOOCOMMERCE COLUMNS (Full Format - Hebrew column names matching WP export)
# =========================

# Build column list dynamically to support multiple attributes
def build_csv_columns():
    base_cols = [
        "ID",
        "Type",
        "SKU",
        "GTIN, UPC, EAN, or ISBN",
        "Name",
        "Published",
        "Is featured?",
        "Visibility in catalog",
        "Short description",
        "Description",
        "Date sale price starts",
        "Date sale price ends",
        "Tax status",
        "Tax class",
        "In stock?",
        "Stock",
        "Low stock amount",
        "Backorders allowed?",
        "Sold individually?",
        "Weight (kg)",
        "Length (cm)",
        "Width (cm)",
        "Height (cm)",
        "Allow customer reviews?",
        "Purchase note",
        "Sale price",
        "Regular price",
        "Categories",
        "Tags",
        "Shipping class",
        "Images",
        "Download limit",
        "Download expiry days",
        "Parent",
        "Grouped products",
        "Upsells",
        "Cross-sells",
        "External URL",
        "Button text",
        "Position",
        "Brands",
    ]

    # Add attribute columns
    for i in range(1, MAX_ATTRIBUTES + 1):
        base_cols.extend([
            f"Attribute {i} name",
            f"Attribute {i} value(s)",
            f"Attribute {i} visible",
            f"Attribute {i} global",
            f"Attribute {i} default",
        ])

    return base_cols


CSV_FIELDS = build_csv_columns()


# =========================
# HELPERS
# =========================

def ensure_dirs():
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)


def normalize(text):
    """Normalize whitespace in text."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def safe_text(el) -> str:
    """Safely get text from a BeautifulSoup element."""
    if el is None:
        return ""
    return normalize(el.get_text(" ", strip=True))


def generate_id(url: str) -> int:
    """Generate a stable numeric ID from URL."""
    return int(hashlib.md5(url.encode()).hexdigest()[:8], 16) % 100000


def sku_from_url(url: str) -> str:
    """Generate SKU from URL slug."""
    slug = urlparse(url).path.strip("/").split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "-", slug).lower()[:40]
    h = hashlib.md5(url.encode()).hexdigest()[:6]
    return f"{slug}-{h}"


def parse_price(text) -> str:
    """Parse price string to number string."""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"[^\d.,]", "", text)
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    m = re.search(r"\d+(\.\d+)?", text)
    return m.group(0) if m else ""


def read_sitemap(xml_path: str) -> List[str]:
    """Read URLs from sitemap XML."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    urls = []
    for el in root.iter():
        if el.tag.endswith("loc") and el.text:
            urls.append(el.text.strip())

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def filter_product_urls(urls: List[str]) -> List[str]:
    """Filter URLs to only include product pages."""
    return [u for u in urls if "/product/" in u.lower()]


# =========================
# JSON-LD EXTRACTION
# =========================

def extract_jsonld_objects(soup: BeautifulSoup) -> List[Any]:
    """Extract all JSON-LD objects from the page."""
    objs = []
    for sc in soup.find_all("script", {"type": "application/ld+json"}):
        raw = sc.string or sc.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
            objs.append(data)
        except Exception:
            continue
    return objs


def find_product_in_jsonld(jsonlds: List[Any]) -> Optional[Dict[str, Any]]:
    """Find Product node in JSON-LD (supports Yoast @graph structure)."""
    for data in jsonlds:
        if isinstance(data, dict):
            # Check @graph array
            items = data.get("@graph", [data])
            if isinstance(items, dict):
                items = [items]
            for item in items:
                if isinstance(item, dict):
                    item_type = item.get("@type", "")
                    if item_type == "Product" or (isinstance(item_type, list) and "Product" in item_type):
                        return item

        # Handle list at top level
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    return item
    return None


# =========================
# PRODUCT DATA EXTRACTION
# =========================

def extract_images(soup: BeautifulSoup, product_node: Optional[Dict]) -> List[str]:
    """Extract all product images."""
    images = []

    # Try JSON-LD first
    if product_node:
        img_data = product_node.get("image")
        if isinstance(img_data, str):
            images.append(img_data)
        elif isinstance(img_data, list):
            for img in img_data:
                if isinstance(img, str):
                    images.append(img)
                elif isinstance(img, dict):
                    url = img.get("url") or img.get("contentUrl")
                    if url:
                        images.append(str(url))
        elif isinstance(img_data, dict):
            url = img_data.get("url") or img_data.get("contentUrl")
            if url:
                images.append(str(url))

    # HTML gallery fallback
    if not images:
        for img in soup.select(".woocommerce-product-gallery img"):
            src = img.get("data-large_image") or img.get("data-src") or img.get("src")
            if src and not src.endswith("placeholder.png"):
                images.append(src)

    # Additional gallery images
    for img in soup.select(".woocommerce-product-gallery__image img"):
        src = img.get("data-large_image") or img.get("data-src") or img.get("src")
        if src and src not in images and not src.endswith("placeholder.png"):
            images.append(src)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for img in images:
        if img not in seen:
            seen.add(img)
            unique.append(img)
    return unique


def extract_categories(soup: BeautifulSoup) -> str:
    """Extract product categories as hierarchical string."""
    categories = []

    # Try breadcrumb first
    breadcrumb = soup.select(".woocommerce-breadcrumb a")
    if breadcrumb:
        cats = []
        for link in breadcrumb[1:]:  # Skip home
            text = safe_text(link)
            if text and text.lower() not in ["home", "בית", "shop", "חנות"]:
                cats.append(text)
        if cats:
            categories.append(" > ".join(cats))

    # Also try product_cat links
    if not categories:
        for link in soup.select(".posted_in a, .product_meta a[rel='tag']"):
            text = safe_text(link)
            if text:
                categories.append(text)

    return ", ".join(categories)


def extract_tags(soup: BeautifulSoup) -> str:
    """Extract product tags."""
    tags = []
    for link in soup.select(".tagged_as a, .product_meta .tag-link"):
        text = safe_text(link)
        if text:
            tags.append(text)
    return ", ".join(tags)


def extract_descriptions(soup: BeautifulSoup, product_node: Optional[Dict]) -> Tuple[str, str]:
    """Extract short description and full description."""
    short_desc = ""
    desc = ""

    # Short description from HTML
    short_el = soup.select_one(".woocommerce-product-details__short-description")
    if short_el:
        short_desc = safe_text(short_el)

    # Full description
    tab_desc = soup.select_one("#tab-description")
    if tab_desc:
        desc = safe_text(tab_desc)
    elif product_node and product_node.get("description"):
        desc = normalize(str(product_node.get("description")))

    # If still empty, try summary paragraph
    if not desc:
        summary_p = soup.select_one(".summary p")
        if summary_p:
            desc = safe_text(summary_p)

    return short_desc, desc


def extract_prices(soup: BeautifulSoup, product_node: Optional[Dict]) -> Tuple[str, str]:
    """Extract regular and sale prices."""
    regular = ""
    sale = ""

    price_box = soup.select_one(".summary .price, .product .price")
    if price_box:
        del_el = price_box.select_one("del")
        ins_el = price_box.select_one("ins")

        if del_el and ins_el:
            regular = parse_price(safe_text(del_el))
            sale = parse_price(safe_text(ins_el))
        else:
            # Single price (check for range)
            price_text = safe_text(price_box)
            # Take first price if range
            regular = parse_price(price_text.split("–")[0].split("-")[0])

    # JSON-LD fallback
    if not regular and product_node:
        offers = product_node.get("offers")
        if isinstance(offers, dict):
            regular = parse_price(offers.get("price"))
        elif isinstance(offers, list) and offers:
            regular = parse_price(offers[0].get("price"))

    return regular, sale


def extract_stock_status(soup: BeautifulSoup, product_node: Optional[Dict]) -> Tuple[int, str]:
    """Extract stock status. Returns (in_stock: 0/1, stock_qty)."""
    # Check HTML classes
    if soup.select_one(".out-of-stock, .stock.out-of-stock"):
        return 0, ""
    if soup.select_one(".in-stock, .stock.in-stock"):
        # Try to get quantity
        stock_el = soup.select_one(".stock")
        if stock_el:
            text = safe_text(stock_el)
            qty_match = re.search(r"(\d+)", text)
            if qty_match:
                return 1, qty_match.group(1)
        return 1, ""

    # JSON-LD fallback
    if product_node:
        offers = product_node.get("offers", {})
        if isinstance(offers, list) and offers:
            offers = offers[0]
        availability = str(offers.get("availability", "")).lower()
        if "outofstock" in availability:
            return 0, ""
        if "instock" in availability:
            return 1, ""

    return 1, ""  # Default to in stock


def build_attribute_value_map(soup: BeautifulSoup) -> Dict[str, Dict[str, str]]:
    """
    Build a mapping of attribute_name -> {value_id: display_name}
    from HTML swatches/selects that have data-value and data-title.

    Example HTML:
    <ul data-attribute_name="attribute_pa_color">
      <li data-value="01" data-title="אדום" title="אדום">...</li>
      <li data-value="02" data-title="לבן" title="לבן">...</li>
    </ul>

    Or from select options:
    <select data-attribute_name="attribute_pa_size">
      <option value="small">קטן</option>
    </select>
    """
    attr_map = {}

    # Method 1: From swatches (ul/li with data-value and data-title)
    for swatch_container in soup.select("[data-attribute_name]"):
        attr_name = swatch_container.get("data-attribute_name", "")
        if not attr_name:
            continue

        # Clean attribute name
        clean_name = attr_name.replace("attribute_pa_", "").replace("attribute_", "")

        if clean_name not in attr_map:
            attr_map[clean_name] = {}

        # Find all items with data-value
        for item in swatch_container.select("[data-value]"):
            value_id = item.get("data-value", "").strip()
            # Try data-title first, then title attribute, then text content
            display_name = (
                    item.get("data-title") or
                    item.get("title") or
                    safe_text(item)
            ).strip()

            if value_id and display_name:
                attr_map[clean_name][value_id] = display_name

    # Method 2: From select dropdowns
    for select in soup.select("select[data-attribute_name], select[name^='attribute']"):
        attr_name = select.get("data-attribute_name") or select.get("name", "")
        clean_name = attr_name.replace("attribute_pa_", "").replace("attribute_", "")

        if clean_name not in attr_map:
            attr_map[clean_name] = {}

        for option in select.select("option[value]"):
            value_id = option.get("value", "").strip()
            display_name = safe_text(option).strip()

            if value_id and display_name and value_id != "":
                attr_map[clean_name][value_id] = display_name

    # Method 3: From variable-items wrapper divs
    for wrapper in soup.select(".variable-items-wrapper"):
        attr_name = wrapper.get("data-attribute_name", "")
        clean_name = attr_name.replace("attribute_pa_", "").replace("attribute_", "")

        if not clean_name:
            continue

        if clean_name not in attr_map:
            attr_map[clean_name] = {}

        for item in wrapper.select(".variable-item"):
            value_id = item.get("data-value", "").strip()
            display_name = (
                    item.get("data-title") or
                    item.get("title") or
                    ""
            ).strip()

            if value_id and display_name:
                attr_map[clean_name][value_id] = display_name

    return attr_map


def translate_attribute_value(attr_name: str, value: str, value_map: Dict[str, Dict[str, str]]) -> str:
    """Translate attribute value ID to display name using the map."""
    clean_name = attr_name.replace("attribute_pa_", "").replace("attribute_", "")

    if clean_name in value_map:
        if value in value_map[clean_name]:
            return value_map[clean_name][value]

    # Return original value if no mapping found
    return value


def extract_attributes(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract product attributes for variable products."""
    attributes = []

    # Build value mapping first
    value_map = build_attribute_value_map(soup)

    # From variations form
    variations_form = soup.select_one("form.variations_form")
    if variations_form:
        # Get attribute data from data-product_variations
        variations_data = variations_form.get("data-product_variations")
        if variations_data:
            try:
                variations = json.loads(variations_data)
                # Handle case where variations might not be a list
                if not isinstance(variations, list):
                    variations = []
                # Collect all attribute names and values
                attr_map = {}
                for var in variations:
                    attrs = var.get("attributes", {})
                    # Handle case where attributes might be False/None instead of dict
                    if not isinstance(attrs, dict):
                        continue
                    for key, val in attrs.items():
                        # key format: attribute_pa_color or attribute_color
                        attr_name = key.replace("attribute_pa_", "").replace("attribute_", "")
                        attr_name_display = attr_name.replace("-", " ").replace("_", " ").title()
                        if attr_name_display not in attr_map:
                            attr_map[attr_name_display] = {"raw_name": attr_name, "values": set()}
                        if val:
                            # Translate value ID to display name
                            display_val = translate_attribute_value(key, val, value_map)
                            attr_map[attr_name_display]["values"].add(display_val)

                for name, data in attr_map.items():
                    attributes.append({
                        "name": name,
                        "values": ", ".join(sorted(data["values"])),
                        "visible": 1,
                        "global": 0,
                        "default": ""
                    })
            except Exception:
                pass

    # Fallback: parse select dropdowns
    if not attributes:
        for row in soup.select(".variations tr, table.variations tr"):
            label = row.select_one("label, th")
            select = row.select_one("select")

            if label and select:
                name = safe_text(label).rstrip(":")
                values = []
                for opt in select.select("option[value]"):
                    val = opt.get("value", "").strip()
                    if val:
                        values.append(val)

                if name and values:
                    attributes.append({
                        "name": name,
                        "values": ", ".join(values),
                        "visible": 1,
                        "global": 0,
                        "default": ""
                    })

    # Also check additional attributes table
    for row in soup.select(".woocommerce-product-attributes tr, .shop_attributes tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if th and td:
            name = safe_text(th)
            value = safe_text(td)
            if name and value:
                # Check if already exists
                exists = any(a["name"].lower() == name.lower() for a in attributes)
                if not exists:
                    attributes.append({
                        "name": name,
                        "values": value,
                        "visible": 1,
                        "global": 0,
                        "default": ""
                    })

    return attributes[:MAX_ATTRIBUTES]


def extract_variations(soup: BeautifulSoup, parent_id: int, parent_name: str, parent_sku: str) -> List[Dict[str, Any]]:
    """Extract all variations from a variable product."""
    variations = []

    variations_form = soup.select_one("form.variations_form")
    if not variations_form:
        return variations

    variations_data = variations_form.get("data-product_variations")
    if not variations_data:
        return variations

    try:
        var_list = json.loads(variations_data)
    except Exception:
        return variations

    # Handle case where var_list might not be a list
    if not isinstance(var_list, list):
        return variations

    # Build value mapping for translating IDs to names
    value_map = build_attribute_value_map(soup)

    for var in var_list:
        var_id = var.get("variation_id", generate_id(str(var)))

        # Build variation name from attributes
        attrs = var.get("attributes", {})
        attr_parts = []
        attr_list = []

        # Handle case where attributes might be False/None instead of dict
        if not isinstance(attrs, dict):
            attrs = {}

        for key, val in attrs.items():
            attr_name = key.replace("attribute_pa_", "").replace("attribute_", "")
            attr_name_display = attr_name.replace("-", " ").replace("_", " ").title()
            if val:
                # Translate value ID to display name
                display_val = translate_attribute_value(key, val, value_map)
                attr_parts.append(display_val)
                attr_list.append({
                    "name": attr_name_display,
                    "value": display_val,
                    "visible": 0,
                    "global": 0,
                    "default": ""
                })

        var_name = f"{parent_name} - {', '.join(attr_parts)}" if attr_parts else parent_name

        # Get variation SKU
        var_sku = var.get("sku", "")
        if not var_sku:
            var_sku = f"{parent_sku}-{var_id}"

        # Prices
        regular_price = parse_price(var.get("display_regular_price", ""))
        sale_price = parse_price(var.get("display_price", ""))

        # If display_price equals regular_price, there's no sale
        if regular_price and sale_price and regular_price == sale_price:
            sale_price = ""
        # If there's a sale, regular should be higher
        if not regular_price and sale_price:
            regular_price = sale_price
            sale_price = ""

        # Stock status
        is_in_stock = 1 if var.get("is_in_stock", True) else 0
        stock_qty = str(var.get("max_qty", "")) if var.get("max_qty") else ""

        # Image
        image = var.get("image", {}).get("full_src", "") or var.get("image", {}).get("src", "")

        variation_row = {
            "ID": var_id,
            "Type": "variation",
            "SKU": var_sku,
            "GTIN, UPC, EAN, or ISBN": "",
            "Name": var_name,
            "Published": 1,
            "Is featured?": 0,
            "Visibility in catalog": "visible",
            "Short description": "",
            "Description": "",
            "Date sale price starts": "",
            "Date sale price ends": "",
            "Tax status": "taxable",
            "Tax class": "parent",
            "In stock?": is_in_stock,
            "Stock": stock_qty,
            "Low stock amount": "",
            "Backorders allowed?": 0,
            "Sold individually?": 0,
            "Weight (kg)": var.get("weight", ""),
            "Length (cm)": var.get("dimensions", {}).get("length", ""),
            "Width (cm)": var.get("dimensions", {}).get("width", ""),
            "Height (cm)": var.get("dimensions", {}).get("height", ""),
            "Allow customer reviews?": 0,
            "Purchase note": "",
            "Sale price": sale_price,
            "Regular price": regular_price,
            "Categories": "",
            "Tags": "",
            "Shipping class": "",
            "Images": image,
            "Download limit": "",
            "Download expiry days": "",
            "Parent": f"id:{parent_id}",
            "Grouped products": "",
            "Upsells": "",
            "Cross-sells": "",
            "External URL": "",
            "Button text": "",
            "Position": "",
            "Brands": "",
        }

        # Add attribute columns for variation
        for i in range(1, MAX_ATTRIBUTES + 1):
            if i <= len(attr_list):
                attr = attr_list[i - 1]
                variation_row[f"Attribute {i} name"] = attr["name"]
                variation_row[f"Attribute {i} value(s)"] = attr["value"]
                variation_row[f"Attribute {i} visible"] = ""
                variation_row[f"Attribute {i} global"] = 0
                variation_row[f"Attribute {i} default"] = ""
            else:
                variation_row[f"Attribute {i} name"] = ""
                variation_row[f"Attribute {i} value(s)"] = ""
                variation_row[f"Attribute {i} visible"] = ""
                variation_row[f"Attribute {i} global"] = ""
                variation_row[f"Attribute {i} default"] = ""

        variations.append(variation_row)

    return variations


# =========================
# MAIN SCRAPING FUNCTION
# =========================

def scrape_product(url: str) -> Optional[List[Dict[str, Any]]]:
    """
    Scrape a product page. Returns list of rows:
    - For simple products: [product_row]
    - For variable products: [parent_row, variation_row1, variation_row2, ...]
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            return None
    except Exception:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract JSON-LD
    jsonlds = extract_jsonld_objects(soup)
    product_node = find_product_in_jsonld(jsonlds)

    # Check if this is actually a product page
    is_product = bool(product_node) or bool(soup.select_one("h1.product_title"))
    if not is_product:
        return None

    # Determine product type
    is_variable = bool(soup.select_one("form.variations_form"))
    product_type = "variable" if is_variable else "simple"

    # Generate ID and SKU
    product_id = generate_id(url)

    # Extract product name
    name = ""
    if product_node and product_node.get("name"):
        name = normalize(str(product_node["name"]))
    else:
        h1 = soup.select_one("h1.product_title")
        if h1:
            name = safe_text(h1)

    # Extract SKU
    sku = ""
    if product_node and product_node.get("sku"):
        sku = normalize(str(product_node["sku"]))
    if not sku:
        sku_el = soup.select_one(".sku")
        if sku_el:
            sku = safe_text(sku_el)
    if not sku:
        sku = sku_from_url(url)

    # Extract other data
    short_desc, description = extract_descriptions(soup, product_node)
    regular_price, sale_price = extract_prices(soup, product_node)
    in_stock, stock_qty = extract_stock_status(soup, product_node)
    images = extract_images(soup, product_node)
    categories = extract_categories(soup)
    tags = extract_tags(soup)
    attributes = extract_attributes(soup)

    # Build main product row
    product_row = {
        "ID": product_id,
        "Type": product_type,
        "SKU": sku,
        "GTIN, UPC, EAN, or ISBN": "",
        "Name": name,
        "Published": 1,
        "Is featured?": 0,
        "Visibility in catalog": "visible",
        "Short description": short_desc,
        "Description": description,
        "Date sale price starts": "",
        "Date sale price ends": "",
        "Tax status": "taxable",
        "Tax class": "",
        "In stock?": in_stock,
        "Stock": stock_qty,
        "Low stock amount": "",
        "Backorders allowed?": 0,
        "Sold individually?": 0,
        "Weight (kg)": "",
        "Length (cm)": "",
        "Width (cm)": "",
        "Height (cm)": "",
        "Allow customer reviews?": 1,
        "Purchase note": "",
        "Sale price": sale_price if product_type == "simple" else "",
        "Regular price": regular_price if product_type == "simple" else "",
        "Categories": categories,
        "Tags": tags,
        "Shipping class": "",
        "Images": ", ".join(images),
        "Download limit": "",
        "Download expiry days": "",
        "Parent": "",
        "Grouped products": "",
        "Upsells": "",
        "Cross-sells": "",
        "External URL": "",
        "Button text": "",
        "Position": 0,
        "Brands": "",
    }

    # Add attribute columns
    for i in range(1, MAX_ATTRIBUTES + 1):
        if i <= len(attributes):
            attr = attributes[i - 1]
            product_row[f"Attribute {i} name"] = attr["name"]
            product_row[f"Attribute {i} value(s)"] = attr["values"]
            product_row[f"Attribute {i} visible"] = attr["visible"]
            product_row[f"Attribute {i} global"] = attr["global"]
            product_row[f"Attribute {i} default"] = attr.get("default", "")
        else:
            product_row[f"Attribute {i} name"] = ""
            product_row[f"Attribute {i} value(s)"] = ""
            product_row[f"Attribute {i} visible"] = ""
            product_row[f"Attribute {i} global"] = ""
            product_row[f"Attribute {i} default"] = ""

    rows = [product_row]

    # Extract variations for variable products
    if is_variable:
        variations = extract_variations(soup, product_id, name, sku)
        rows.extend(variations)

    return rows


# =========================
# CSV WRITER
# =========================

def write_csv_header():
    """Write CSV header row."""
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()


def append_csv_rows(rows: List[Dict[str, Any]]):
    """Append rows to CSV file."""
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})


# =========================
# MAIN
# =========================

def main():
    ensure_dirs()

    # Check input file
    if not os.path.exists(INPUT_XML):
        print(f"ERROR: Input file not found: {os.path.abspath(INPUT_XML)}")
        print("Please place your sitemap XML file in the 'input' directory as 'products.xml'")
        return

    # Read and filter URLs
    print(f"Reading sitemap: {INPUT_XML}")
    urls = read_sitemap(INPUT_XML)
    product_urls = filter_product_urls(urls)

    print(f"Found {len(urls)} total URLs, {len(product_urls)} product URLs")

    if not product_urls:
        print("No product URLs found. Make sure URLs contain '/product/'")
        return

    # Initialize CSV
    write_csv_header()

    # Process products
    ok = 0
    skip = 0
    total_rows = 0

    for i, url in enumerate(product_urls, 1):
        try:
            rows = scrape_product(url)

            if not rows:
                skip += 1
                print(f"[{i}/{len(product_urls)}] SKIP :: {url}")
                continue

            append_csv_rows(rows)
            ok += 1
            total_rows += len(rows)

            product_type = rows[0].get("Type", "simple")
            var_count = len(rows) - 1 if product_type == "variable" else 0

            print(f"[{i}/{len(product_urls)}] OK ({product_type}" +
                  (f"+{var_count}vars" if var_count else "") + f") :: {url}")

        except Exception as e:
            skip += 1
            print(f"[{i}/{len(product_urls)}] ERROR :: {url} - {type(e).__name__}: {e}")

        time.sleep(SLEEP_SEC)

    print("\n" + "=" * 50)
    print("DONE!")
    print(f"Products scraped: {ok}")
    print(f"Total rows (incl. variations): {total_rows}")
    print(f"Skipped: {skip}")
    print(f"Output: {os.path.abspath(OUTPUT_CSV)}")


if __name__ == "__main__":
    main()