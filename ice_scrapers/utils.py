from bs4 import BeautifulSoup
import re
from typing import Tuple
from utils import (
    logger,
    session,
)


def special_facilities(facility: dict) -> dict:
    """
    Some very specific facilities have unique fixes
    that are hard to fit into our normal repair_* pattern.

    Please don't expand this function unless it's necessary
    """
    match facility["name"]:
        case "Naval Station Guantanamo Bay (JTF Camp Six and Migrant Ops Center Main A)":
            """
            First special case? JTF Camp Six is purely a mess.
            While we work on getting a consistent address for this facility,
            we'll need to make the two records converge.
            """
            facility["address"]["country"] = "Cuba"
            facility["address"]["administrative_area"] = "FPO"
            facility["address"]["locality"] = "FPO"
            facility["address"]["postal_code"] = "34009"
            facility["address"]["street"] = "AVENUE C PSC 1005 BOX 55"
        case "JTF CAMP SIX":
            facility["address"]["country"] = "Cuba"
            facility["address"]["administrative_area"] = "FPO"
            facility["name"] = "Naval Station Guantanamo Bay (JTF Camp Six and Migrant Ops Center Main A)"
        case _:
            pass
    return facility


def repair_name(name: str, locality: str) -> Tuple[str, bool]:
    """Even facility names are occasionally bad"""
    matches = [
        {"match": "ALEXANDRIA STAGING FACILI", "replace": "Alexandria Staging Facility", "locality": "ALEXANDRIA"},
        {"match": "ORANGE COUNTY JAIL (NY)", "replace": "ORANGE COUNTY JAIL", "locality": "GOSHEN"},
        {"match": "NORTH LAKE CORRECTIONAL F", "replace": "NORTH LAKE CORRECTIONAL FACILITY", "locality": "BALDWIN"},
        {"match": "PHELPS COUNTY JAIL (MO)", "replace": "Phelps County Jail", "locality": "ROLLA"},
        {
            "match": "PENNINGTON COUNTY JAIL (SOUTH DAKOTA)",
            "replace": "PENNINGTON COUNTY JAIL",
            "locality": "RAPID CITY",
        },
        {
            "match": "CORR. CTR OF NORTHWEST OHIO",
            "replace": "CORRECTIONS CENTER OF NORTHWEST OHIO",
            "locality": "STRYKER",
        },
        {
            "match": "FOLKSTON D RAY ICE PROCES",
            "replace": "D. RAY JAMES CORRECTIONAL INSTITUTION",
            "locality": "FOLKSTON",
        },
        {"match": "COLLIER COUNTY NAPLES JAIL CENTER", "replace": "COLLIER COUNTY JAIL", "locality": "NAPLES"},
        {
            "match": "IAH SECURE ADULT DETENTION FACILITY (POLK)",
            "replace": "IAM SECURE ADULT DET. FACILITY",
            "locality": "LIVINGSTON",
        },
        {"match": "CIMMARRON CORR FACILITY", "replace": "CIMMARRON CORRECTIONAL FACILITY", "locality": "CUSHING"},
        {"match": "ORANGE COUNTY JAIL (FL)", "replace": "ORANGE COUNTY JAIL", "locality": "ORLANDO"},
        {"match": "CLARK COUNTY JAIL (IN)", "replace": "CLARK COUNTY JAIL", "locality": "JEFFERSONVILLE"},
        {"match": "PRINCE EDWARD COUNTY (FARMVILLE)", "replace": "ICA - FARMVILLE", "locality": "FARMVILLE"},
        {"match": "PHELPS COUNTY JAIL (NE)", "replace": "PHELPS COUNTY JAIL", "locality": "HOLDREGE"},
        {
            "match": "WASHINGTON COUNTY JAIL (PURGATORY CORRECTIONAL FAC",
            "replace": "WASHINGTON COUNTY JAIL",
            "locality": "HURRICANE",
        },
        {"match": "ETOWAH COUNTY JAIL (ALABAMA)", "replace": "ETOWAH COUNTY JAIL", "locality": "GADSDEN"},
        {"match": "BURLEIGH COUNTY", "replace": "BURLEIGH COUNTY JAIL", "locality": "BISMARCK"},
        {"match": "NELSON COLEMAN CORRECTION", "replace": "NELSON COLEMAN CORRECTIONS CENTER", "locality": "KILLONA"},
        {
            "match": "CIMMARRON CORR FACILITY",
            "replace": "CIMARRON CORRECTIONAL FACILITY",
            "locality": "CUSHING",
        },
        {
            "match": "IAM SECURE ADULT DET. FACILITY",
            "replace": "IAH SECURE ADULT DET. FACILITY",
            "locality": "LIVINGSTON",
        },
    ]
    cleaned = False
    for m in matches:
        if m["match"] == name and m["locality"] == locality:
            name = m["replace"]
            cleaned = True
            break
    return name, cleaned


def repair_street(street: str, locality: str = "") -> Tuple[str, bool]:
    """Generally, we'll let the spreadsheet win arguments just to be consistent"""
    street_filters = [
        # address mismatch between site and spreadsheet
        {"match": "80 29th Street", "replace": "100 29th Street", "locality": "Brooklyn"},
        {"match": "2250 Laffoon Trl", "replace": "2250 Lafoon Trail", "locality": "Madisonville"},
        {"match": "560 Gum Springs Road", "replace": "560 Gum Spring Road", "locality": "Winnfield"},
        {
            "match": "Vincente Taman Building",
            "replace": "Vicente T Seman Bldg Civic Center",
            "locality": "Susupe, Saipan",
        },
        {"match": "209 County Road A049", "replace": "209 County Road 49", "locality": "Estancia"},
        {
            "match": "50140 US Highway 191 South",
            "replace": "50140 UNITED STATES HIGHWAY 191 SOUTH",
            "locality": "Rock Springs",
        },
        {"match": "5 Basler Drive", "replace": "5 BASLER DR", "locality": "Ste. Genevieve"},
        {"match": "3843 Stagg Ave", "replace": "3843 Stagg Avenue", "locality": "Basile"},
        {
            "match": "13880 Business Center Drive NW",
            "replace": "13880 Business Center Drive",
            "locality": "Elk River",
        },
        {"match": "3040 South State Route 100", "replace": "3040 SOUTH STATE HIGHWAY 100", "locality": "Tiffin"},
        {"match": "1001 San Rio Blvd", "replace": "1001 San Rio Boulevard", "locality": "Laredo"},
        {"match": "1209 Sunflower Lane", "replace": "1209 Sunflower Ln", "locality": "Alvarado"},
        {"match": "27991 Buena Vista Blvd.", "replace": "27991 BUENA VISTA BOULEVARD", "locality": "Los Fresnos"},
        {"match": "175 Pike County Blvd.", "replace": "175 PIKE COUNTY BOULEVARD", "locality": "Lords Valley"},
        {"match": "500 W. 2nd Street", "replace": "301 W. 2nd", "locality": "Rolla"},
        {"match": "3405 West Highway 146", "replace": "3405 W HWY 146", "locality": "LaGrange"},
        {"match": "1623 E J Street, Suite 2", "replace": "1623 E. J STREET", "locality": "Tacoma"},
        {"match": "1805 W 32nd Street", "replace": "1805 W 32ND ST", "locality": "Baldwin"},
        {"match": "500 Hilbig Road", "replace": "500 HILBIG RD", "locality": "Conroe"},
        {"match": "806 Hilbig Road", "replace": "806 HILBIG RD", "locality": "Conroe"},
        {"match": "425 Golden State Avenue", "replace": "425 Golden State Ave", "locality": "Bakersfield"},
        {"match": "832 East Texas HWY 44", "replace": "832 EAST TEXAS STATE HIGHWAY 44", "locality": "Encinal"},
        {"match": "18201 SW 12th Street", "replace": "18201 SW 12TH ST", "locality": "Miami"},
        {"match": "2190 E Mesquite Avenue", "replace": "2190 EAST MESQUITE AVENUE", "locality": "Pahrump"},
        {"match": "287 Industrial Drive", "replace": "327 INDUSTRIAL DRIVE", "locality": "Jonesboro"},
        {"match": "1572 Gateway Road", "replace": "1572 GATEWAY", "locality": "Calexico"},
        {"match": "1199 N Haseltine Road", "replace": "1199 N HASELTINE RD", "locality": "Springfield"},
        {"match": "1701 North Washington", "replace": "1701 NORTH WASHINGTON ST", "locality": "Grand Forks"},
        {"match": "611 Frontage Road", "replace": "611 FRONTAGE RD", "locality": "McFarland"},
        {"match": "12450 Merritt Road", "replace": "12450 MERRITT DR", "locality": "Chardon"},
        {"match": "411 S. Broadway Avenue", "replace": "411 SOUTH BROADWAY AVENUE", "locality": "Albert Lea"},
        {"match": "3424 Hwy 252 E", "replace": "3424 HIGHWAY 252 EAST", "locality": "Folkston"},
        {"match": "3250 N. Pinal Parkway", "replace": "3250 NORTH PINAL PARKWAY", "locality": "Florence"},
        {"match": "351 Elliott Street", "replace": "351 ELLIOTT ST", "locality": "Honolulu"},
        {"match": "1 Success Loop Rd", "replace": "1 SUCCESS LOOP DR", "locality": "Berlin"},
        {"match": "700 Arch Street", "replace": "700 ARCH ST", "locality": "Philadelphia"},
        {"match": "1300 Metropolitan", "replace": "1300 METROPOLITAN AVE", "locality": "Leavenworth"},
        {"match": "601 McDonough Blvd SE", "replace": "601 MCDONOUGH BOULEVARD SE", "locality": "Atlanta"},
        {"match": "1705 E Hanna Rd", "replace": "1705 EAST HANNA RD", "locality": "Eloy"},
        {"match": "2255 East 8th North", "replace": "2255 E 8TH NORTH", "locality": "Mountain Home"},
        {"match": "8915 Montana Avenue", "replace": "8915 MONTANA AVE", "locality": "El Paso"},
        {"match": "704 E Broadway Street", "replace": "702 E BROADWAY ST", "locality": "Eden"},
        {"match": "1300 E Hwy 107", "replace": "1330 HIGHWAY 107", "locality": "La Villa"},
        {"match": "216 W. Center Street", "replace": "215 WEST CENTRAL STREET", "locality": "Juneau"},
        {"match": "300 El Rancho Way ", "replace": "300 EL RANCHO WAY", "locality": "Dilley"},
        {"match": "3130 North Oakland Street", "replace": "3130 OAKLAND ST", "locality": "Aurora"},
        {"match": "03151 Co. Rd. 24.2", "replace": "3151 ROAD 2425 ROUTE 1", "locality": "Stryker"},
        {"match": "20 Hobo Forks Road", "replace": "20 HOBO FORK RD", "locality": "Natchez"},
        {"match": "7340 Highway 26 W", "replace": "7340 HIGHWAY 26 WEST", "locality": "Oberlin"},
        {"match": "1400 E Fourth Ave", "replace": "1400 E 4TH AVE", "locality": "Anchorage"},
        {"match": "3900 N. Powerline Road", "replace": "3900 NORTH POWERLINE ROAD", "locality": "Pompano Beach"},
        {"match": "185 E. Michigan Street", "replace": "185 EAST MICHIGAN AVENUE", "locality": "Battle Creek"},
        {"match": "601 Central Avenue", "replace": "601 CENTRAL AVE", "locality": "Newport"},
        {"match": "501 E Court Avenue", "replace": "501 EAST COURT AVE", "locality": "Jeffersonville"},
        {"match": "3200 S. Kings Hwy", "replace": "3700 S KINGS HWY", "locality": "Cushing"},
        {"match": "301 South Walnut", "replace": "301 SOUTH WALNUT STREET", "locality": "Cottonwood Falls"},
        {"match": "830 Pine Hill Road", "replace": "830 PINEHILL ROAD", "locality": "Jena"},
        {
            "match": "11093 SW Lewis Memorial Dr",
            "replace": "11093 SW LEWIS MEMORIAL DRIVE",
            "locality": "Bowling Green",
        },
        {"match": "58 Pine Mountain Road", "replace": "58 PINE MOUNTAIN RD", "locality": "McElhattan"},
        {
            "match": "Adelanto East 10400 Rancho Road | Adelanto West 10250 Rancho Road",
            "replace": "10250 Rancho Road",
            "locality": "Adelanto",
        },
        {"match": "4702 East Saunders", "replace": "4702 EAST SAUNDERS STREET", "locality": "Laredo"},
        {"match": "9998 S. Highway 98", "replace": "9998 SOUTH HIGHWAY 83", "locality": "Laredo"},
        # a unique one, 'cause the PHONE NUMBER IS IN THE ADDRESS?!
        {"match": "911 PARR BLVD 775 328 3308", "replace": "911 E Parr Blvd", "locality": "RENO"},
        # fix a few bad addresses in spreadsheet
        {"match": "33 NE 4 STREET", "replace": "33 NE 4th Street", "locality": "MIAMI"},
        {"match": "DEPARTMENT OF CORRECTIONS 1618 ASH STREET", "replace": "1618 Ash Street", "locality": "ERIE"},
        {"match": "203 ASPINAL AVE. PO BOX 3236", "replace": "203 Aspinall Avenue", "locality": "HAGATNA"},
        {
            "match": "11866 HASTINGS BRIDGE ROAD P.O. BOX 429",
            "replace": "11866 Hastings Bridge Road",
            "locality": "LOVEJOY",
        },
        {"match": "300 KANSAS CITY STREET NONE", "replace": "307 Saint Joseph St", "locality": "RAPID CITY"},
        {"match": "4909 FM 2826", "replace": "4909 Farm to Market Road", "locality": "ROBSTOWN"},
        {"match": "6920 DIGITAL RD", "replace": "11541 Montana Avenue", "locality": "EL PASO"},
        # default matches should come last
    ]
    cleaned = False
    for f in street_filters:
        if (f["match"] in street) and ((f["locality"] and f["locality"] == locality) or not f["locality"]):
            street = street.replace(f["match"], f["replace"])
            cleaned = True
            break
    # simpler loop for default cleanup
    default_matches = [
        {"match": "'s", "replace": ""},
        {"match": ".", "replace": ""},
        {"match": ",", "replace": ""},
    ]
    for f in default_matches:
        if f["match"] in street:
            street = street.replace(f["match"], f["replace"])
            cleaned = True
    return street, cleaned


def repair_zip(zip_code: int, locality: str) -> Tuple[str, bool]:
    """
    Excel does a cool thing where it strips leading 0s
    Also, many zip codes are mysteriously discordant
    """
    zcode = str(zip_code)
    cleaned = False
    # don't replace an empty zip with all 0s
    if 0 < len(zcode) < 5:
        # pad any prefix
        zeros = "0" * (5 - len(zcode))
        zcode = f"{zeros}{zcode}"
        return zcode, cleaned
    matches = [
        {"match": "89512", "replace": "89506", "locality": "Reno"},
        {"match": "82901", "replace": "82935", "locality": "Rock Springs"},
        {"match": "98421-1615", "replace": "98421", "locality": "Tacoma"},
        {"match": "89048", "replace": "89060", "locality": "Pahrump"},
        {"match": "85132", "replace": "85232", "locality": "Florence"},
        # Laredo facility addresses are particularly bad...
        {"match": "78041", "replace": "78401", "locality": "LAREDO"},
        {"match": "78401", "replace": "78046", "locality": "LAREDO"},
    ]
    for z in matches:
        if z["match"] == zcode and z["locality"] == locality:
            zcode = z["replace"]
            cleaned = True
            break
    return zcode, cleaned


def repair_locality(locality: str, administrative_area: str) -> Tuple[str, bool]:
    """
    There is no consistency with any address.
    How the post office ever successfully delivered a letter is beyond me
    """
    cleaned = False
    matches = [
        {"match": "LaGrange", "replace": "La Grange", "area": "KY"},
        {"match": "Leachfield", "replace": "LEITCHFIELD", "area": "KY"},
        {"match": "SAIPAN", "replace": "Susupe, Saipan", "area": "MP"},
        {"match": "COTTONWOOD FALL", "replace": "Cottonwood Falls", "area": "KS"},
        {"match": "Sault Ste. Marie", "replace": "SAULT STE MARIE", "area": "MI"},
    ]
    for f in matches:
        if f["match"] == locality and f["area"] == administrative_area:
            locality = f["replace"]
            cleaned = True
            break
    return locality, cleaned


def update_facility(old: dict, new: dict) -> dict:
    """Recursive function to Insert values from new when they are false-y in old"""
    for k, v in new.items():
        if isinstance(v, dict):
            old[k] = update_facility(old[k], new[k])
        if not old.get(k, None):
            old[k] = v
    return old


def get_ice_scrape_pages(url: str) -> list:
    """
    Discover all facility pages
    This _may_ be generic to Drupal's pagination code...
    """
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    links = soup.findAll("a", href=re.compile(r"\?page="))
    if not links:
        raise Exception(f"{url} contains *no* links?!")
    pages = [
        f"{url}{link['href']}&exposed_form_display=1"
        for link in links
        if not any(k in link["aria-label"] for k in ["Next", "Last"])
    ]
    logger.debug("Pages discovered: %s", pages)
    return pages
