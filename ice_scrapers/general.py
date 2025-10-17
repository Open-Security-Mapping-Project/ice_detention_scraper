import copy
from ice_scrapers import (
    insert_additional_facilities,
    load_sheet,
    merge_field_offices,
    scrape_facilities,
    scrape_field_offices,
)
from schemas import facilities_schema


def facilities_scrape_wrapper(keep_sheet: bool = True, force_download: bool = True) -> dict:
    facilities_data = copy.deepcopy(facilities_schema)
    facilities = load_sheet(keep_sheet, force_download)
    facilities_data["facilities"] = copy.deepcopy(facilities)
    facilities_data = scrape_facilities(facilities_data)
    field_offices = scrape_field_offices()
    facilities_data = merge_field_offices(facilities_data, field_offices)
    facilities_data = insert_additional_facilities(facilities_data)

    return facilities_data
