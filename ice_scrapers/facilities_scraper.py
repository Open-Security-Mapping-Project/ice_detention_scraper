from bs4 import BeautifulSoup
import copy
import datetime
import re
from ice_scrapers import (
    get_ice_scrape_pages,
    repair_locality,
    repair_street,
    repair_zip,
    repair_name,
    special_facilities,
    update_facility,
)
from schemas import facility_schema
import time
from utils import (
    default_timestamp,
    logger,
    session,
    timestamp_format,
)

base_scrape_url = "https://www.ice.gov/detention-facilities"


def scrape_facilities(facilities_data: dict) -> dict:
    """Scrape all ICE detention facility data from all discovered pages"""
    start_time = time.time()
    logger.info("Starting to scrape ICE.gov detention facilities...")
    facilities_data["scraped_date"] = datetime.datetime.now(datetime.UTC)
    urls = get_ice_scrape_pages(base_scrape_url)

    scraped_count = 0
    for page_num, url in enumerate(urls):
        logger.info("Scraping page %s/%s...", page_num + 1, len(urls))
        try:
            facilities = _scrape_page(url)
        except Exception as e:
            logger.error("Error scraping page %s: %s", page_num + 1, e)
        logger.debug("Found %s facilities on page %s", len(facilities), page_num + 1)
        time.sleep(1)  # Be respectful to the server
        scraped_count += len(facilities)
        for facility in facilities:
            facility = special_facilities(facility)
            addr = facility["address"]
            street, cleaned = repair_street(addr["street"], addr["locality"])
            if cleaned:
                addr["street"] = street
                facility["_repaired_record"] = True
            zcode, cleaned = repair_zip(addr["postal_code"], addr["locality"])
            if cleaned:
                addr["postal_code"] = zcode
                facility["_repaired_record"] = True
            locality, cleaned = repair_locality(addr["locality"], addr["administrative_area"])
            if cleaned:
                addr["locality"] = locality
                facility["_repaired_record"] = True
            name, cleaned = repair_name(facility["name"], addr["locality"])
            if cleaned:
                facility["name"] = name
                facility["_repaired_record"] = True
            full_address = ",".join([street, locality, addr["administrative_area"], zcode]).upper()
            if not facility["address_str"]:
                facility["address_str"] = full_address
            if full_address in facilities_data["facilities"].keys():  # type: ignore [attr-defined]
                facilities_data["facilities"][full_address] = update_facility(  # type: ignore [index]
                    facilities_data["facilities"][full_address],  # type: ignore [index]
                    facility,
                )
                # update to the frequently nicer address from ice.gov
                facilities_data["facilities"][full_address]["address"] = addr  # type: ignore [index]
                # add scraped urls
                for url in facility["source_urls"]:
                    # no dupes
                    if url in facilities_data["facilities"][full_address]["source_urls"]:  # type: ignore [index]
                        continue
                    facilities_data["facilities"][full_address]["source_urls"].append(url)  # type: ignore [index]
            # this is likely to produce _some_ duplicates, but it's a reasonable starting place
            else:
                facilities_data["facilities"][facility["name"]] = facility  # type: ignore [index]

    facilities_data["scrape_runtime"] = time.time() - start_time
    logger.info("Total facilities scraped: %s", scraped_count)
    logger.info(" Completed in %s seconds", facilities_data["scrape_runtime"])
    return facilities_data


def _scrape_updated(url: str) -> datetime.datetime:
    """
    Scrape url to get "last updated" time
    Is specifically oriented around ice.gov facility pages
    """
    if not url:
        logger.error("Could not find a time block! Guessing wildly!")
        return datetime.datetime.strptime(default_timestamp, timestamp_format)
    logger.debug("  Fetching: %s", url)
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error("  Error parsing %s: %s", url, e)
        return datetime.datetime.strptime(default_timestamp, timestamp_format)
    soup = BeautifulSoup(response.content, "html.parser")
    times = soup.findAll("time")
    if not times:
        logger.error("Could not find a time block! Guessing wildly!")
        return datetime.datetime.strptime(default_timestamp, timestamp_format)
    # RFC8601 "UTC offset in the form ±HH:MM[:SS[.ffffff]]" is not supported (2025-09-04) in python's strptime implementation
    timestamp = times[0].get("datetime", default_timestamp)
    timestamp, tz = timestamp.rsplit("-", 1)
    tz = tz.replace(":", "")
    # another hack...we'll assume a US timestamp here...
    timestamp = f"{timestamp}-+{tz}"
    return datetime.datetime.strptime(timestamp, timestamp_format)


def _scrape_page(page_url: str) -> list:
    """Scrape a single page of facilities using BeautifulSoup"""
    logger.debug("  Fetching: %s", page_url)
    try:
        response = session.get(page_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error("  Error parsing %s: %s", page_url, e)
        return []

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    facilities = []

    # Look for the main content area - ICE uses different possible containers
    content_selectors = [
        "div.view-content",  # Primary content container
        "div.views-rows",  # Alternative container
        "ul.views-rows",  # List-based container
        "div.region-content",  # Region content
        "main",  # HTML5 main element
        "div.content",  # Generic content
    ]
    content_container = None
    logger.debug("Searching %s for content", page_url)
    for selector in content_selectors:
        content_container = soup.select_one(selector)
        if content_container:
            logger.debug("  Found content using selector: %s", selector)
            break

    if not content_container:
        logger.warning("  Warning: Could not find content container, searching entire page")
        content_container = soup

    # Look for facility entries - try multiple patterns
    facility_selectors = [
        "li.grid",  # List items with grid class
        "div.views-row",  # View rows
        "li.views-row",  # List-based view rows
        "div.facility-item",  # Custom facility items
        "article",  # Article elements
        "div.node",  # Drupal node containers
    ]
    facility_elements: list = []
    for selector in facility_selectors:
        elements = content_container.select(selector)
        if elements:
            facility_elements = elements
            logger.debug(
                "  Found %s facility elements using selector: %s",
                len(elements),
                selector,
            )
            break

    if not facility_elements:
        # Fallback: look for any element containing facility-like text patterns
        logger.warning("  Using fallback: searching for facility patterns in text")
        facility_elements = _find_facility_patterns(content_container)

    # Extract data from each facility element
    for element in facility_elements:
        facility_data = _extract_single_facility(element, page_url)
        if facility_data and facility_data.get("name"):
            facilities.append(facility_data)

    logger.info("  Extracted %s facilities from page", len(facilities))
    return facilities


def _find_facility_patterns(container):
    """Fallback method to find facility data using text patterns"""
    facility_elements = []

    # Look for text patterns that indicate facilities
    facility_patterns = [
        r"([A-Z][^|]+(?:\|[^|]+)?)\s*([A-Z][^A-Z]*Field Office)",
        r"([^-]+)\s*-\s*([A-Z][^A-Z]*Field Office)",
    ]

    text_content = container.get_text()

    for pattern in facility_patterns:
        matches = re.findall(pattern, text_content, re.MULTILINE)
        for match in matches:
            # Create a pseudo-element with the matched text
            pseudo_element = type(
                "Element",
                (),
                {
                    "text": f"{match[0]} {match[1]}",
                    "get_text": lambda: f"{match[0]} {match[1]}",
                    "select": lambda x: [],
                    "select_one": lambda x: None,
                    "find": lambda *args, **kwargs: None,
                    "find_all": lambda *args, **kwargs: [],
                },
            )()
            facility_elements.append(pseudo_element)

    return facility_elements


def _extract_single_facility(element, page_url):
    """Extract data from a single facility element"""
    facility = copy.deepcopy(facility_schema)
    raw_scrape = str(element)
    facility["source_urls"].append(page_url)
    logger.debug("Trying to get facility data from %s", element)
    # Method 1: Try structured extraction if element has proper HTML structure
    name = element.select_one(".views-field-title")
    if name:
        facility["name"] = name.text
    field_office = element.select_one(".views-field-field-field-office-name")
    if field_office:
        # St. Paul Field Office -> St Paul Field Office
        facility["field_office"]["field_office"] = field_office.text.strip(".")
    address = element.select_one(".address-line1")
    if address:
        facility["address"]["street"] = address.text
    locality = element.select_one(".locality")
    if locality:
        facility["address"]["locality"] = locality.text
    administrative_area = element.select_one(".administrative-area")
    if administrative_area:
        facility["address"]["administrative_area"] = administrative_area.text
    postal_code = element.select_one(".postal-code")
    if postal_code:
        facility["address"]["postal_code"] = postal_code.text
    country = element.select_one(".country")
    if country:
        facility["address"]["country"] = country.text
    phone = element.select_one(".ct-addr")
    if phone:
        facility["phone"] = phone.text

    # Method 2: If structured extraction failed, parse the text content
    if not facility["name"] or not facility["field_office"]:
        logger.warning("Falling back to text scraping!")
        facility = _parse_facility_text(raw_scrape, facility)

    # Extract image URL using the specified nested structure
    image_element = element.findAll("img")
    if image_element:
        facility["image_url"] = f"https://www.ice.gov{image_element[0]['src']}"
    facility_url_element = element.findAll("a")
    facility_url = ""
    if facility_url_element:
        facility_url = f"https://www.ice.gov{facility_url_element[0]['href']}"
        facility["source_urls"].append(facility_url)
    if facility_url:
        facility["page_updated_date"] = _scrape_updated(facility_url)
    # Clean up extracted data
    facility = _clean_facility_data(facility)

    logger.debug("Returning %s", facility)
    return facility


def _clean_facility_data(facility):
    """Clean up data (currently a no-op)"""
    return facility


def _parse_facility_text(text, facility):
    """Parse facility information from raw text"""
    # Common patterns for ICE facility listings
    patterns = [
        # Pattern: "Facility Name | Other NameField Office"
        r"^([^|]+(?:\|[^|]+)?)\s*([A-Z][^A-Z]*Field Office)",
        # Pattern: "Facility Name Field Office"
        r"^([^A-Z]*[^-]+?)\s*([A-Z][^A-Z]*Field Office)",
        # Pattern: "- Facility NameField Office"
        r"^-\s*([^-]+?)\s*([A-Z][^A-Z]*Field Office)",
    ]

    facility_info = None
    for pattern in patterns:
        match = re.match(pattern, text, re.MULTILINE | re.DOTALL)
        if match:
            facility_info = match
            break

    if facility_info:
        facility["name"] = facility_info.group(1).strip()
        facility["field_office"] = facility_info.group(2).strip()
        if facility["name"].endswith(" St."):
            facility["name"] = facility["name"].rstrip(" St.")
            facility["field_office"] = f"St. {facility['field_office']}"
        if facility["name"].endswith(" San"):
            facility["name"] = facility["name"].rstrip(" San")
            facility["field_office"] = f"San {facility['field_office']}"
        # Extract address from remaining text
        remaining_text = text[facility_info.end() :].strip()
        address_lines = []
        phone = ""
        for line in remaining_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            line = re.search(r"(.*United States).*$", line).group(1)
            logger.debug("Processing %s", line)
            # Check if it's a phone number
            if re.match(r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$", line):
                phone = line
            # Check if it looks like an address component
            elif (
                any(
                    indicator in line.lower()
                    for indicator in [
                        "street",
                        "road",
                        "avenue",
                        "drive",
                        "blvd",
                        "highway",
                        "hwy",
                    ]
                )
                or re.match(r"^\d+\s", line)  # Starts with number
                or re.search(r"\b[A-Z]{2}\s+\d{5}", line)  # Contains state and zip
                or "United States" in line
            ):
                address_lines.append(line)

        if address_lines:
            facility["address"] = ", ".join(address_lines)
        facility["phone"] = phone
    return facility
