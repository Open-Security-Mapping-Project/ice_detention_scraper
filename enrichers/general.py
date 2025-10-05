from concurrent.futures import ProcessPoolExecutor
import copy
from enrichers import (
    openstreetmap,
    wikidata,
    wikipedia,
)
from schemas import (
    facilities_schema,
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
        for res in pool.map(_enrich_facility, facilities_data["facilities"].items()):
            enriched_data["facilities"][res[0]] = res[1]  # type: ignore [index]
            processed += 1
            logger.info("  -> Finished %s, %s/%s completed", res[1]["name"], processed, total)

    logger.info("Data enrichment completed!")
    enriched_data["enrich_runtime"] = time.time() - start_time
    logger.info(" Completed in %s seconds", enriched_data["enrich_runtime"])
    return enriched_data


def _enrich_facility(facility_data: tuple) -> tuple:
    """enrich a single facility"""
    facility_id, facility = facility_data
    facility_name = facility["name"]
    if len(facility["source_urls"]) == 1 and "vera-institute/ice-detention-trends" in facility["source_urls"][0]:
        logger.debug("  Skipping enrichment of facility with only vera.org data: %s", facility["name"])
        return facility_id, facility
    logger.info("Enriching facility %s...", facility_name)
    enriched_facility = copy.deepcopy(facility)

    wiki_res = wikipedia.Wikipedia(facility_name=facility_name).search()
    wd_res = wikidata.Wikidata(facility_name=facility_name).search()
    osm = openstreetmap.OpenStreetMap(facility_name=facility_name, address=facility.get("address", {}))
    osm_res = osm.search()
    url = wiki_res.get("url", None)
    if url:
        enriched_facility["wikipedia"]["page_url"] = url
    enriched_facility["wikipedia"]["search_query"] = wiki_res.get("search_query_steps", "")
    url = wd_res.get("url", None)
    if url:
        enriched_facility["wikidata"]["page_url"] = url
    enriched_facility["wikidata"]["search_query"] = wd_res.get("search_query_steps", "")
    lat = osm_res.get("details", {}).get("latitude", None)
    long = osm_res.get("details", {}).get("longitude", None)
    if lat:
        enriched_facility["osm"]["latitude"] = lat
    if long:
        enriched_facility["osm"]["longitude"] = lat
    url = osm_res.get("url", None)
    if url:
        enriched_facility["osm"]["url"] = url
    enriched_facility["osm"]["search_query"] = osm_res.get("search_query_steps", "")

    logger.debug(enriched_facility)
    return facility_id, enriched_facility
