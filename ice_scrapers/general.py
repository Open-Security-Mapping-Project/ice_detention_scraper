import copy
from thefuzz import fuzz  # type: ignore [import-untyped]
from schemas import facilities_schema
from .agencies import scrape_agencies
from .custom_facilities import insert_additional_facilities
from .facilities_scraper import scrape_facilities
from .field_offices import (
    merge_field_offices,
    scrape_field_offices,
)
from .inspections import find_inspections
from .spreadsheet_load import load_sheet
from .vera_data import collect_vera_facility_data
from utils import logger


def facilities_scrape_wrapper(
    keep_sheet: bool = True,
    force_download: bool = True,
    skip_vera: bool = False,
    inspection_text: bool = False,
) -> tuple[dict, dict]:
    agencies = scrape_agencies(keep_sheet, force_download)
    facilities_data = copy.deepcopy(facilities_schema)
    facilities = load_sheet(keep_sheet, force_download)
    facilities_data["facilities"] = copy.deepcopy(facilities)
    facility_name_map = {v["name"].lower(): k for k, v in facilities_data["facilities"].items()}
    inspections = find_inspections(keep_text=inspection_text)
    facilities_data = scrape_facilities(facilities_data)

    # actually attach inspections to facilities
    for facility, inspect in inspections.items():
        logger.debug("  Matching %s for inspection details...", facility)
        # exact match (extremely unlikely)
        if facility.lower() in facility_name_map:
            """
            flip the order so the newest inspection is likely first in the list
            because trying to convert these wildly inconsistent dates to sortable
            objects is probably a fool's errand, so we'll just hope for the best...
            """
            facilities_data["facilities"][facility_name_map[facility.lower()]]["inspection"]["details"] = copy.deepcopy(
                inspect
            ).reverse()
            break
        # logger.debug("    Checking fuzzy matches:")
        for k, v in facility_name_map.items():
            r = fuzz.partial_ratio(facility, k)
            # logger.debug("    %s === %s, ratio: %s", facility, k, r)
            if r > 80:
                logger.debug("  Probably the right facility %s => %s, (ratio %s)", k, facility, r)
                facilities_data["facilities"][facility_name_map[k]]["inspection"]["details"] = copy.deepcopy(inspect)
                break

    if not skip_vera:
        facilities_data = collect_vera_facility_data(facilities_data, keep_sheet, force_download)
    field_offices = scrape_field_offices()
    facilities_data = merge_field_offices(facilities_data, field_offices)
    facilities_data = insert_additional_facilities(facilities_data)

    return facilities_data, agencies
