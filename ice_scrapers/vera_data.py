import copy
from ice_scrapers import ice_facility_types
import os
import polars
from schemas import facility_schema
from utils import (
    logger,
    output_folder,
    req_get,
)

# Github can aggressively rate-limit requests, so this may fail in surprising ways!
base_url = (
    "https://raw.githubusercontent.com/vera-institute/ice-detention-trends/refs/heads/main/metadata/facilities.csv"
)
filename = f"{output_folder}{os.sep}vera_facilities.csv"


def _vera_name_fixes(name: str, city: str) -> tuple[str, bool]:
    """Match Vera names with ice.gov names"""
    matches = [
        {"match": "Adams County", "replace": "Adams County Courthouse", "city": "Ritzville"},
        {"match": "Lemon Creek, Juneau,AK", "replace": "Lemon Creek Correctional Facility", "city": "Juneau"},
        {"match": "Dept Of Corrections-Hagatna", "replace": "Department of Corrections Hagatna", "city": "Hagatna"},
        {"match": "Essex Co. Jail, Middleton", "replace": "Essex County Jail", "city": "Middleton"},
        {"match": "Etowah County Jail (AL)", "replace": "Etowah County Jail", "city": "Gadsden"},
        {"match": "Fairfax Co Jail", "replace": "Fairfax County Jail", "city": "Fairfax"},
        {
            "match": "Ft Lauderdale Behavor Hlth Ctr",
            "replace": "Fort Lauderdale Behavioral Health Center",
            "city": "Oakland Park",
        },
        {"match": "Marion Correctional Inst.", "replace": "Marion Correctional Institution", "city": "Ocala"},
        {"match": "Florida St. Pris.", "replace": "Florida State Prison", "city": "Raiford"},
        {"match": "Dade Correctional Inst", "replace": "Dade Correctional Institution", "city": "Florida City"},
        {"match": "Franklin County Jail, VT", "replace": "Franklin County Jail", "city": "Saint Albans"},
        {"match": "Frederick County Det. Cen", "replace": "Frederick County Detention Center", "city": "Frederick"},
        {"match": "Freeborn County Jail, MN", "replace": "Freeborn Adult Detention Center", "city": "Albert Lea"},
        {"match": "Fremont County Jail, CO", "replace": "Fremont County Jail", "city": "Canon City"},
        {"match": "Fremont County Jail, WY", "replace": "Fremont County Jail", "city": "Lander"},
        {
            "match": "Grand Forks County Correc",
            "replace": "Grand Forks County Correctional Facility",
            "city": "Grand Forks",
        },
        {"match": "Grand Forks Co. Juvenile", "replace": "Grand Forks County Juvenile Facility", "city": "Grand Forks"},
        {"match": "Haile Det. Center", "replace": "Haile Detention Center", "city": "Caldwell"},
        {"match": "Hampden Co.House Of Corr.", "replace": "Hampden County House of Corrections", "city": "Ludlow"},
        {"match": "Eloy Federal Contract Fac", "replace": "Eloy Federal Contract Facility", "city": "Eloy"},
        {
            "match": "Henderson County Det. Fac.",
            "replace": "Henderson County Detention Facility",
            "city": "Hendersonville",
        },
        {"match": "Hel District Custody", "replace": "Helena District Custody", "city": "Helena"},
        {"match": "Houston Contract Det.Fac.", "replace": "Houston Contract Detention Facility", "city": "Houston"},
        {"match": "Howard County Det Cntr", "replace": "Howard County Detention Center", "city": "Jessup"},
        {"match": "In Dept. Of Corrections", "replace": "Indiana Department of Corrections", "city": "Indianapolis"},
        {"match": "Beth Israel Hospital, Manhattan", "replace": "Beth Israel Hospital Manhattan", "city": "New York"},
        {"match": "Kent Co.,Grand Rapids,MI", "replace": "Kent County Jail", "city": "Grand Rapids"},
        {"match": "Kern County Jail (Lerdo)", "replace": "Kern County Jail", "city": "Bakersfield"},
        {"match": "Lackawana Cnty Jail, PA", "replace": "Lackawana County Jail", "city": "Scranton"},
        {"match": "Las Colinas Women Det Fac", "replace": "Las Colinas Women's Detention Facility", "city": "Santee"},
        {"match": "Lawrence Co. Jail, SD", "replace": "Lawrence County Jail", "city": "Deadwood"},
        {"match": "Lehigh County Jail, PA", "replace": "Lehigh County Jail", "city": "Allentown"},
        {"match": "Macomb Co.Mt.Clemens,MI.", "replace": "Macomb County Jail", "city": "Mount Clemens"},
        {"match": "Bwater St Hosp Bridgewate", "replace": "Bridgewater State Hospital", "city": "Bridgewater"},
        {"match": "Meade Co. Jail, SD", "replace": "Meade County Jail", "city": "Sturgis"},
        {"match": "Mecklenburg (NC) Co Jail", "replace": "Mecklenburg County Jail", "city": "Charlotte"},
        {"match": "Mountrail Co. Jail, ND", "replace": "Mountrail County Jail", "city": "Stanley"},
        {
            "match": "Saipan Department Of Corrections",
            "replace": "SAIPAN DEPARTMENT OF CORRECTIONS (SUSUPE)",
            "city": "Saipan",
        },
        {"match": "Sitka City Jail, Sitka AK", "replace": "Sitka City Jail", "city": "Sitka"},
        {"match": "Leavenworth USP", "replace": "Leavenworth US Penitentiary", "city": "Leavenworth"},
        {"match": "Limestone County Jail", "replace": "Limestone County Detention Center", "city": "Groesbeck"},
        {"match": "FCI Berlin", "replace": "Berlin Fed. Corr. Inst.", "city": "Berlin"},
        {"match": "Nassau Co Correc Center", "replace": "Nassau County Correctional Center", "city": "East Meadow"},
        {"match": "Riverside Reg Jail", "replace": "Riverside Regional Jail", "city": "Hopewell"},
        {"match": "T Don Hutto Residential Center", "replace": "T Don Hutto Detention Center", "city": "Taylor"},
        {"match": "Desert View", "replace": "Desert View Annex", "city": "Adelanto"},
        {"match": "Alamance Co. Det. Facility", "replace": "Alamance County Detention Facility", "city": "Graham"},
        {"match": "Hall County Sheriff", "replace": "Hall County Department of Corrections", "city": "Grand Island"},
        {"match": "Hall County Sheriff", "replace": "Hall County Department of Corrections", "city": "Grand Island"},
        {
            "match": "Dallas County Jail-Lew Sterrett",
            "replace": "Dallas County Jail - Lew Sterrett Justice Center",
            "city": "Dallas",
        },
        {"match": "Hardin Co Jail", "replace": "Hardin County Jail", "city": "Eldora"},
        {"match": "Washington County Jail", "replace": "Washington County Detention Center", "city": "Fayetteville"},
        {"match": "Robert A Deyton Detention Fac", "replace": "Robert A Deyton Detention Facility", "city": "Lovejoy"},
        {"match": "Anchorage Jail", "replace": "Anchorage Correctional Complex", "city": "Anchorage"},
        {"match": "Douglas Co. Wisconsin", "replace": "Douglas County", "city": "Superior"},
        {
            "match": "Imperial Regional Adult Det Fac",
            "replace": "Imperial Regional Detention Facility",
            "city": "Calexico",
        },
        {"match": "Erie County Jail, PA", "replace": "Erie County Jail", "city": "Erie"},
        {"match": "NW ICE Processing Ctr", "replace": "Northwest ICE Processing Center", "city": "Tacoma"},
        {"match": "Richwood Cor Center", "replace": "Richwood Correctional Center", "city": "Monroe"},
        {"match": "Krome North SPC", "replace": "Krome North Service Processing Center", "city": "Miami"},
        {"match": "Calhoun Co., Battle Cr,MI", "replace": "Calhoun County Correctional Center", "city": "Battle Creek"},
        {"match": "Dodge County Jail, Juneau", "replace": "Dodge County Jail", "city": "Juneau"},
        {"match": "Kandiyohi Co. Jail", "replace": "Kandiyohi County Jail", "city": "Willmar"},
        {
            "match": "California City Corrections Center",
            "replace": "California City Correctional Center",
            "city": "California City",
        },
        {"match": "Plymouth Co Cor Facilty", "replace": "Plymouth County Correctional Facility", "city": "Plymouth"},
        {"match": "Otero Co Processing Center", "replace": "Otero County Processing Center", "city": "Chaparral"},
        {"match": "Strafford Co Dept Of Corr", "replace": "Strafford County Corrections", "city": "Dover"},
        {"match": "Madison Co. Jail, MS.", "replace": "Madison County Jail", "city": "Canton"},
        {
            "match": "South Texas Fam Residential Center",
            "replace": "Dilley Immigration Processing Center",
            "city": "Dilley",
        },
        {"match": "Tulsa County Jail", "replace": "Tulsa County Jail (David L. Moss Justice Ctr)", "city": "Tulsa"},
        {"match": "Kenton Co Detention Ctr", "replace": "Kenton County Jail", "city": "Covington"},
        {"match": "Pennington County Jail SD", "replace": "Pennington County Jail", "city": "Rapid City"},
        {"match": "Denver Contract Det. Fac.", "replace": "Denver Contract Detention Facility", "city": "Aurora"},
        {
            "match": "Corrections Center of NW Ohio",
            "replace": "Corrections Center of Northwest Ohio",
            "city": "Stryker",
        },
        {"match": "Grayson County Detention Center", "replace": "Grayson County Jail", "city": "Leitchfield"},
        {"match": "Chippewa Co, SSM", "replace": "Chippewa County SSM", "city": "Sault Sainte Marie"},
        {"match": "Florence SPC", "replace": "Florence Service Processing Center", "city": "Florence"},
        {"match": "D. Ray James Prison", "replace": "D. Ray James Correctional Institution", "city": "Folkston"},
        {"match": "Collier County Sheriff", "replace": "Collier County Jail", "city": "Naples"},
        {"match": "Oldham County Jail", "replace": "Oldham County Detention Center", "city": "La Grange"},
        {"match": "Salt Lake County Jail", "replace": "Salt Lake County Metro Jail", "city": "Salt Lake City"},
        {"match": "Annex Folkston IPC", "replace": "Folkston Annex IPC", "city": "Folkston"},
        {
            "match": "Northwest State Correctional Ctr.",
            "replace": "Northwest State Correctional Center",
            "city": "Swanton",
        },
        {"match": "Basile Detention Center", "replace": "South Louisiana ICE Processing Center", "city": "Basile"},
        {"match": "New Hanover Co Det Center", "replace": "New Hanover County Jail", "city": "Castle Hayne"},
        {"match": "Bluebonnet Det Fclty", "replace": "Bluebonnet Detention Facility", "city": "Anson"},
        {"match": "San Luis Regional Det Center", "replace": "San Luis Regional Detention Center", "city": "San Luis"},
        {"match": "Buffalo SPC", "replace": "Buffalo Service Processing Center", "city": "Batavia"},
        {"match": "Laurel County Corrections", "replace": "Laurel County Correctional Center", "city": "London"},
        {"match": "Coastal Bend Det. Facility", "replace": "Coastal Bend Detention Facility", "city": "Robstown"},
        {"match": "Winn Corr Institute", "replace": "Winn Correctional Center", "city": "Winnfield"},
        {"match": "Elizabeth Contract D.F.", "replace": "Elizabeth Contract Detention Faciilty", "city": "Elizabeth"},
        {
            "match": "Chittenden Reg. Cor. Facility",
            "replace": "Chittenden Regional Correctional Facility",
            "city": "South Burlington",
        },
        {
            "match": "NW Regional Corrections Center",
            "replace": "Northwest Regional Corrections Center",
            "city": "Crookston",
        },
        {
            "match": "Lasalle ICE Processing Center",
            "replace": "Central Louisiana ICE Processing Center (CLIPC)",
            "city": "Jena",
        },
        {
            "match": "La Salle Co Regional Det. Center",
            "replace": "La Salle County Regional Detention Center",
            "city": "Encinal",
        },
        {
            "match": "Hancock Co Pub Sfty Cplx",
            "replace": "Hancock County Public Safety Complex",
            "city": "Bay St. Louis",
        },
        {"match": "Brooks County Jail (Contract)", "replace": "Brooks County Jail", "city": "Falfurrias"},
        {"match": "Burleigh Co. Jail, ND", "replace": "Burleigh County Jail", "city": "Bismarck"},
        {"match": "Lubbock County Jail", "replace": "Lubbock County Detention Center", "city": "Lubbock"},
        {"match": "Montgomery County Jail", "replace": "Montgomery Ice Processing Center", "city": "Conroe"},
        {"match": "Sebastian County Det Cnt", "replace": "Sebastian County Detention Center", "city": "Fort Smith"},
        {"match": "Atlanta U.S. Pen.", "replace": "FCI Atlanta", "city": "Atlanta"},
        {"match": "Clinton County Corr. Fac.", "replace": "Clinton County Correctional Facility", "city": "Mcelhattan"},
        {
            "match": "Freeborn County Jail, MN",
            "replace": "Freeborn County Adult Detention Center",
            "city": "Albert Lea",
        },
    ]
    fixed = False
    for m in matches:
        if m["match"] == name and m["city"] == city:
            fixed = True
            name = m["replace"]
            break
    return name, fixed


def _vera_city_fixes(city: str, state: str) -> tuple[str, bool]:
    """There are a few cases where getting a state match requires some munging"""
    matches = [
        {"match": "Saipan", "replace": "Susupe, Saipan", "city": "MP"},
        {"match": "Sault Sainte Marie", "replace": "Sault Ste Marie", "city": "MP"},
    ]
    fixed = False
    for m in matches:
        if m["match"] == city and m["city"] == state:
            fixed = True
            city = m["replace"]
            break
    return city, fixed


def collect_vera_facility_data(facilities_data: dict, keep_sheet: bool = True, force_download: bool = True) -> dict:
    logger.info("Collecting and extracting data from vera.org facility data...")
    if force_download or not os.path.exists(filename):
        res = req_get(base_url, timeout=120, stream=True)
        size = len(res.content)
        with open(filename, "wb") as f:
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        logger.debug("Wrote %s byte sheet to %s", size, filename)
    df = polars.read_csv(has_header=True, raise_if_empty=True, source=filename, use_pyarrow=True)
    if df.is_empty():
        raise ValueError("Empty CSV loaded somehow! %s", df)
    # first step to removing duplicates is easy, but unlikely to actually filter anything
    df = df.unique()
    logger.debug("Extracted data: %s", df)
    """
    We retrieve the following columns
    detention_facility_code, detention_facility_name, latitude, longitude, city, state, type_detailed, type_grouped

    There are definitely rows that are _essentially_ duplicates, but aren't actually duplicates?
    A single facility (based on the latitude/longitudes) will show up with multiple names in this dataset

    None of the data Vera provides on a facility is more accurate than data we already have, so the logic
    here should be _purely_ "if not exists, add".
    """
    matched_count = 0
    skipped_count = 0
    fixed = 0
    for row in df.iter_rows(named=True):
        if not row["state"] or not row["city"]:
            logger.warning("  Skipping Vera row with missing values: %s", row)
            skipped_count += 1
            continue
        found = False
        facility_name, fixed_name = _vera_name_fixes(row["detention_facility_name"], row["city"])
        row["name"] = facility_name
        city, fixed_city = _vera_city_fixes(row["city"], row["state"])
        row["city"] = city
        if fixed_name or fixed_city:
            fixed += 1
        if row["name"] == "JTF Camp Six":
            row["state"] = "FPO"
            row["city"] = "FPO"
            row["name"] = "Naval Station Guantanamo Bay (JTF Camp Six and Migrant Ops Center Main A)"
        addr_str = f"{row['name']},{row['city']},{row['state']}"
        for k, v in facilities_data["facilities"].items():
            if (
                v["name"].upper() == row["name"].upper()
                and v["address"]["administrative_area"].upper() == row["state"].upper()
                and v["address"]["locality"].upper() == row["city"].upper()
            ):
                logger.debug("  Found matching facility %s...", v["name"])
                facilities_data["facilities"][k]["osm"]["latitude"] = row["latitude"]
                facilities_data["facilities"][k]["osm"]["longitude"] = row["longitude"]
                facilities_data["facilities"][k]["vera_id"] = row["detention_facility_code"]
                facilities_data["facilities"][k]["source_urls"].append(base_url)
                if fixed_name or fixed_city:
                    facilities_data["facilities"][k]["_repaired_record"] = True
                matched_count += 1
                found = True
                break
        if not found:
            facilities_data["facilities"][addr_str] = copy.deepcopy(facility_schema)
            facilities_data["facilities"][addr_str]["source_urls"].append(base_url)
            facilities_data["facilities"][addr_str]["name"] = row["name"]
            facilities_data["facilities"][addr_str]["address"]["administrative_area"] = row["state"]
            facilities_data["facilities"][addr_str]["address"]["locality"] = row["city"]
            facilities_data["facilities"][addr_str]["address_str"] = addr_str
            facilities_data["facilities"][addr_str]["osm"]["latitude"] = row["latitude"]
            facilities_data["facilities"][addr_str]["osm"]["longitude"] = row["longitude"]
            facilities_data["facilities"][addr_str]["facility_type"]["id"] = row["type_detailed"]
            facilities_data["facilities"][addr_str]["facility_type"]["group"] = row["type_grouped"]
            facilities_data["facilities"][addr_str]["vera_id"] = row["detention_facility_code"]
            ft_details = ice_facility_types.get(row["type_detailed"], {})
            if ft_details:
                facilities_data["facilities"][addr_str]["facility_type"]["description"] = ft_details["description"]
                facilities_data["facilities"][addr_str]["facility_type"]["expanded_name"] = ft_details["expanded_name"]
            if fixed_name or fixed_city:
                facilities_data["facilities"][addr_str]["_repaired_record"] = True

    logger.info(
        "  Found %s facilities: Skipped %s, Matched %s, corrected names on %s",
        df.height,
        skipped_count,
        matched_count,
        fixed,
    )
    if not keep_sheet:
        os.unlink(filename)
    return facilities_data
