from concurrent.futures import ProcessPoolExecutor
import copy
from enrichers import (
    openstreetmap,
    wikidata,
    wikipedia,
)
from schemas import (
    default_coords,
    facilities_schema,
    OSM_DELAY,
    WIKIDATA_DELAY,
    WIKIPEDIA_DELAY,
)
import time
from utils import logger


def enrich_facility_data(facilities_data: dict, workers: int = 3) -> dict:
    """wrapper function for multiprocessing of facility enrichment"""
    start_time = time.time()
    logger.info("Starting data enrichment with external sources...")
    enriched_data = copy.deepcopy(facilities_schema)
    total = len(facilities_data["facilities"])
    processed = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        for res in pool.map(enrich_facility, facilities_data["facilities"].items()):
            enriched_data["facilities"][res[0]] = res[1]  # type: ignore [index]
            processed += 1
            logger.info("  -> Finished %s, %s/%s completed", res[1]["name"], processed, total)

    logger.info("Data enrichment completed!")
    enriched_data["enrich_runtime"] = time.time() - start_time
    logger.info(" Completed in %s seconds", enriched_data["enrich_runtime"])
    return enriched_data


def enrich_facility(facility_data: tuple) -> tuple:
    """enrich a single facility"""
    facility_id, facility = facility_data
    facility_name = facility["name"]
    logger.info("Enriching facility %s...", facility_name)
    enriched_facility = copy.deepcopy(facility)

    wiki_res = wikipedia.Wikipedia(facility_name=facility_name, wait_time=WIKIPEDIA_DELAY).search()
    wd_res = wikidata.Wikidata(facility_name=facility_name, wait_time=WIKIDATA_DELAY).search()
    osm_res = openstreetmap.OpenStreetMap(
        facility_name=facility_name, address=facility.get("address", {}), wait_time=OSM_DELAY
    ).search()
    enriched_facility["wikipedia"]["page_url"] = wiki_res.get("url", "")
    enriched_facility["wikipedia"]["search_query"] = wiki_res.get("search_query_steps", "")
    enriched_facility["wikidata"]["page_url"] = wd_res.get("url", "")
    enriched_facility["wikidata"]["search_query"] = wd_res.get("search_query_steps", "")
    enriched_facility["osm"]["latitude"] = osm_res.get("details", {}).get("latitude", default_coords["latitude"])
    enriched_facility["osm"]["longitude"] = osm_res.get("details", {}).get("longitude", default_coords["longitude"])
    enriched_facility["osm"]["url"] = osm_res.get("url", "")
    enriched_facility["osm"]["search_query"] = osm_res.get("search_query_steps", "")

    logger.debug(enriched_facility)
    return facility_id, enriched_facility
