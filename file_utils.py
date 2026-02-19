import copy
import json
import os
from schemas import enrichment_print_schema
from utils import (
    convert_to_dataframe,
    logger,
    output_folder,
)
import xlsxwriter  # type: ignore [import-untyped]


def export_to_file(
    facilities_data: dict,
    filename: str = "ice_detention_facilities_enriched",
    file_type: str = "csv",
) -> str:
    if not facilities_data or not facilities_data.get("facilities", []):
        logger.warning("No data to export!")
        return ""
    full_name = f"{output_folder}{os.sep}{filename}.{file_type}"
    if file_type in ["csv", "xlsx", "parquet"]:
        writer = convert_to_dataframe(facilities_data["facilities"])
        match file_type:
            case "xlsx":
                # Excel doesn't support timezones properly, so...
                with xlsxwriter.Workbook(full_name, {"remove_timezone": True}) as wb:
                    _ = writer.write_excel(workbook=wb, include_header=True, autofit=True)
            case "csv":
                with open(full_name, "w", newline="", encoding="utf-8") as f_out:
                    _ = writer.write_csv(file=f_out, include_header=True)
            case "parquet":
                writer.write_parquet(full_name, use_pyarrow=True)
            case _:
                logger.warning("Invalid dataframe output type %s", file_type)
    elif file_type == "json":
        with open(full_name, "w", encoding="utf-8") as f_out:
            json.dump(facilities_data, f_out, indent=2, sort_keys=True, default=str)

    logger.info(
        "%s file '%s' created successfully with %s facilities.",
        file_type,
        full_name,
        len(facilities_data["facilities"]),
    )
    return filename


def print_summary(facilities_data: dict) -> None:
    """Print summary statistics about the facilities"""
    if not facilities_data:
        logger.info("No data to summarize!")
        logger.info("\n=== ICE Detention Facilities Scraper: Run completed ===")
        return

    total_facilities = len(facilities_data["facilities"])
    logger.info("\n=== ICE Detention Facilities Scraper Summary ===")
    logger.info("Scraped data at %s", facilities_data["scraped_date"])
    logger.info("Total facilities: %s", total_facilities)

    # Count by field office
    field_offices: dict = {}
    for facility_id, facility in facilities_data["facilities"].items():
        office = facility.get("field_office", {}).get("field_office", "Unknown")
        field_offices[office] = field_offices.get(office, 0) + 1

    logger.info("\nFacilities by Field Office:")
    for office, count in sorted(field_offices.items(), key=lambda x: x[1], reverse=True):
        logger.info("  %s: %s", office, count)

    # Check enrichment data if available
    enrich_data = copy.deepcopy(enrichment_print_schema)
    enrich_data["wiki_found"] = sum(
        1 for f in facilities_data["facilities"].values() if f.get("wikipedia", {}).get("page_url", None)
    )
    enrich_data["wikidata_found"] = sum(
        1 for f in facilities_data["facilities"].values() if f.get("wikidata", {}).get("page_url", None)
    )
    enrich_data["osm_found"] = sum(
        1 for f in facilities_data["facilities"].values() if f.get("osm", {}).get("url", None)
    )

    if any(v > 0 for v in enrich_data.values()):
        logger.info("\n=== External Data Enrichment Results ===")
        logger.info(
            "Wikipedia pages found: %s/%s (%s%%)",
            enrich_data["wiki_found"],
            total_facilities,
            enrich_data["wiki_found"] / total_facilities * 100,
        )
        logger.info(
            "Wikidata entries found: %s/%s (%s%%)",
            enrich_data["wikidata_found"],
            total_facilities,
            enrich_data["wikidata_found"] / total_facilities * 100,
        )
        logger.info(
            "OpenStreetMap results found: %s/%s (%s%%)",
            enrich_data["osm_found"],
            total_facilities,
            enrich_data["osm_found"] / total_facilities * 100,
        )

        # Debug information if available
        logger.info("\n=== Wikipedia Debug Information ===")
        false_positives = 0
        errors = 0
        for facility in facilities_data["facilities"].values():
            query: str = facility.get("wikipedia", {}).get("search_query", "")
            if "REJECTED" in query:
                false_positives += 1
            elif "ERROR" in query:
                errors += 1

            if false_positives:
                logger.info("False positives detected and rejected: %s", false_positives)
            if errors:
                logger.info("Search errors encountered: %s", errors)
            if false_positives or errors:
                logger.info("Details: %s", facility.get("wikipedia_search_query", ""))

    logger.info("\n=== ICE Detention Facilities Scraper: Run completed ===")
