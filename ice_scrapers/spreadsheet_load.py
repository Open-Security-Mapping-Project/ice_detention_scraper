from bs4 import BeautifulSoup
import copy
import datetime
from ice_scrapers import (
    ice_facility_types,
    ice_inspection_types,
)
import os
import polars
import re
from schemas import (
    facility_schema,
    field_office_schema,
)
from utils import (
    logger,
    output_folder,
    req_get,
)
from .utils import (
    download_file,
    repair_locality,
    repair_name,
    repair_street,
    repair_zip,
    special_facilities,
)

base_xlsx_url = "https://www.ice.gov/detain/detention-management"
filename = f"{output_folder}{os.sep}detentionstats.xlsx"
# extracted ADP sheet header list 2025-11-07
# These headers periodically change. (eg the FY headers.)
facility_sheet_header = [
    "Name",
    "Address",
    "City",
    "State",
    "Zip",
    "AOR",
    "Type Detailed",
    "Male/Female",
    "YEAR ALOS",
    "Level A",
    "Level B",
    "Level C",
    "Level D",
    "Male Crim",
    "Male Non-Crim",
    "Female Crim",
    "Female Non-Crim",
    "ICE Threat Level 1",
    "ICE Threat Level 2",
    "ICE Threat Level 3",
    "No ICE Threat Level",
    "Mandatory",
    "Guaranteed Minimum",
    "Last Inspection Type",
    "Last Inspection End Date",
    "Last Inspection Standard",
    "Last Final Rating",
]
required_cols = [
    "Name",
    "Address",
    "City",
    "State",
    "Zip",
    "AOR",
    "Type Detailed",
]


def _download_sheet(keep_sheet: bool = True, force_download: bool = True) -> tuple[polars.DataFrame, str]:
    """Download the detention stats sheet from ice.gov"""
    resp = req_get(base_xlsx_url, timeout=120)
    soup = BeautifulSoup(resp.content, "html.parser")
    links = soup.findAll("a", href=re.compile("^https://www.ice.gov/doclib.*xlsx"))
    if not links:
        raise Exception(f"Could not find any XLSX files on {base_xlsx_url}")
    fy_re = re.compile(r".+FY(\d{2}).+")
    # this is _usually_ the most recently uploaded sheet...
    actual_link = links[0]["href"]
    cur_year = int(datetime.datetime.now().strftime("%y"))
    fy = f"FY{cur_year}"
    # try to find the most recent
    for link in links:
        match = fy_re.search(link["href"])
        if not match:
            continue
        year = int(match.group(1))
        if year >= cur_year:
            actual_link = link["href"]
            # this seems like tracking into the future...
            cur_year = year
            fy = f"FY{cur_year}"
    logger.debug("Found sheet at: %s", actual_link)
    if force_download or not os.path.exists(filename):
        logger.info("Downloading detention stats sheet from %s", actual_link)
        download_file(actual_link, filename)
    df = polars.read_excel(
        drop_empty_rows=True,
        drop_empty_cols=False,
        has_header=False,
        raise_if_empty=True,
        # because we're manually defining the column headers...
        read_options={"column_names": [f.replace("YEAR", fy) for f in facility_sheet_header]},
        sheet_name=f"Facilities {fy}",
        source=open(filename, "rb"),
    )
    if not keep_sheet:
        os.unlink(filename)
    return df, actual_link


def load_sheet(keep_sheet: bool = True, force_download: bool = True) -> dict:
    logger.info("Collecting initial facility data from %s", base_xlsx_url)
    df, sheet_url = _download_sheet(keep_sheet, force_download)
    """Convert the detentionstats sheet data into something we can update our facilities with"""
    results: dict = {}
    # occassionally a phone number shows up in weird places in the spreadsheet.
    # let's capture it
    phone_re = re.compile(r".+(\d{3}\s\d{3}\s\d{4})$")
    for row in df.iter_rows(named=True):
        # skip all rows that don't manage to populate all required headers
        if not all(row[k] is not None for k in required_cols):
            logger.debug("Skipping bad row in spreadsheet: %s", row)
            continue
        if row["Name"] == "Name":
            logger.debug("Skipping bad header row: %s", row)
            continue
        # logger.debug("processing %s", row)
        details = copy.deepcopy(facility_schema)
        zcode, cleaned, other_zips = repair_zip(row["Zip"], row["City"])
        details["address"]["other_postal_codes"].extend(other_zips)
        if cleaned:
            details["_repaired_record"] = True
        street, cleaned, other_st = repair_street(row["Address"], row["City"])
        details["address"]["other_streets"].extend(other_st)
        if cleaned:
            details["_repaired_record"] = True
        match = phone_re.search(row["Address"])
        if match:
            if details.get("phone", None):
                details["other_phones"].append(details["phone"])
            details["phone"] = match.group(1)
            details["_repaired_record"] = True
        locality, cleaned, other_city = repair_locality(row["City"], row["State"])
        details["address"]["other_localities"].extend(other_city)
        if cleaned:
            details["_repaired_record"] = True
        name, cleaned, other_names = repair_name(row["Name"], row["City"])
        details["other_names"].extend(other_names)
        if cleaned:
            details["_repaired_record"] = True
        details["address"]["administrative_area"] = row["State"]
        details["address"]["locality"] = locality
        details["address"]["postal_code"] = zcode
        details["address"]["street"] = street
        details["name"] = name
        details = special_facilities(details)
        full_address = ",".join(
            [
                details["address"]["street"],
                details["address"]["locality"],
                details["address"]["administrative_area"],
                details["address"]["postal_code"],
            ]
        ).upper()

        """
        population statistics
        """
        details["population"]["male"]["criminal"] = row["Male Crim"]
        details["population"]["male"]["non_criminal"] = row["Male Non-Crim"]
        details["population"]["female"]["criminal"] = row["Female Crim"]
        details["population"]["female"]["non_criminal"] = row["Female Non-Crim"]
        details["population"]["total"] = (
            row["Male Crim"] + row["Male Non-Crim"] + row["Female Crim"] + row["Female Non-Crim"]
        )
        if row["Male/Female"]:
            if "/" in row["Male/Female"]:
                details["population"]["female"]["allowed"] = True
                details["population"]["male"]["allowed"] = True
            elif row["Male/Female"] == "Female":
                details["population"]["female"]["allowed"] = True
            else:
                details["population"]["male"]["allowed"] = True
        details["population"]["ice_threat_level"] = {
            "level_1": row["ICE Threat Level 1"],
            "level_2": row["ICE Threat Level 2"],
            "level_3": row["ICE Threat Level 3"],
            "none": row["No ICE Threat Level"],
        }
        # Levels extracted from https://www.ice.gov/doclib/detention/FY25_detentionStats09112025.xlsx 2025-09-22
        details["population"]["security_threat"]["low"] = row["Level A"]
        details["population"]["security_threat"]["medium_low"] = row["Level B"]
        details["population"]["security_threat"]["medium_high"] = row["Level C"]
        details["population"]["security_threat"]["high"] = row["Level D"]
        details["population"]["housing"]["mandatory"] = row["Mandatory"]
        details["population"]["housing"]["guaranteed_min"] = row["Guaranteed Minimum"]
        details["population"]["avg_stay_length"] = row["FY26 ALOS"]

        details["facility_type"] = {
            "id": row["Type Detailed"],
        }
        ft_details = ice_facility_types.get(row["Type Detailed"], {})
        if ft_details:
            details["facility_type"]["description"] = ft_details["description"]
            details["facility_type"]["expanded_name"] = ft_details["expanded_name"]
        details["inspection"] = {
            # fall back to type code
            "last_type": ice_inspection_types.get(row["Last Inspection Type"], row["Last Inspection Type"]),
            "last_date": row["Last Inspection End Date"],
            "last_rating": row["Last Final Rating"],
        }
        details["source_urls"].append(sheet_url)
        details["field_office"] = copy.deepcopy(field_office_schema)
        details["field_office"]["id"] = row["AOR"]
        details["address_str"] = full_address
        results[full_address] = details
    logger.info("  Loaded %s facilities", len(results.keys()))
    return results
