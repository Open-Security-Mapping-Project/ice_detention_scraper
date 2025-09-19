#!/usr/bin/env python3
"""
ICE Detention Facilities Data Scraper and Enricher

This script scrapes ICE detention facility data from ICE.gov and enriches it
with information from Wikipedia, Wikidata, and OpenStreetMap.

Usage:
    python main.py --scrape          # Scrape fresh data from ICE website
    python main.py --enrich          # Enrich existing data with external sources
    python main.py --scrape --enrich # Do both operations
    python main.py --help            # Show help

    # Enable debugging
    python main.py --load-existing --enrich --debug

    # With custom output file
    python main.py --load-existing --enrich --debug -o debug_facilities.csv
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import copy
import logging
from file_utils import export_to_file, print_summary
import default_data
from enricher import ExternalDataEnricher
from schemas import supported_output_types
from scraper import ICEGovFacilityScraper
from field_offices import ICEFieldOfficeScraper
from utils import logger
# CLI, argument parsing, script orchestration

# argparse ArgumentParser converts hyphens to underscores.
# @see https://docs.python.org/3/library/argparse.html


def main() -> None:
    parser = ArgumentParser(
        description="ICE Detention Facilities Data Scraper and Enricher",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        default=False,
        help="Scrape initial facility data from ICE.gov",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        default=False,
        help="enrich collected data",
    )
    parser.add_argument(
        "--load-existing",
        action="store_true",
        default=False,
        help="load data from local files",
    )
    parser.add_argument(
        "--file-type",
        default="csv",
        choices=supported_output_types,
        help="type of file to export",
    )
    parser.add_argument(
        "--output-file-name",
        "-o",
        default="ice_detention_facilities",
        help="The file we'll write data out to (excluding the suffix)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Full debug information and logging",
    )
    # todo these need more attention, but should now be accepted as command line options now.
    parser.add_argument(
        "--debug-wikipedia",
        action="store_true",
        help="Add another column on export for Wikipedia debugging details and redirects",
    )
    parser.add_argument(
        "--debug-wikidata",
        action="store_true",
        help="Add another column on export for Wikidata debugging details and redirects",
    )
    parser.add_argument(
        "--debug-osm",
        action="store_true",
        help="Add another column on export for OpenStreetMap debugging details and redirects",
    )

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info("ICE Detention Facilities Scraper by the Open Security Mapping Project. MIT License.")

    if not any([args.scrape, args.enrich, args.load_existing]):
        parser.print_help()
        return

    # todo. temporary notice for debug arguments.
    if args.debug_wikipedia or args.debug_wikidata or args.debug_osm:
        logger.warning(
            "Warning: --debug-wikipedia, --debug-wikidata and --debug-osm are currently not implemented as command line options."
        )

    facilities_data = {}

    if args.scrape and args.load_existing:
        logger.error("Can't scrape and load existing data!")
        exit(1)

    if args.scrape:
        fo_scraper = ICEFieldOfficeScraper()
        field_offices = fo_scraper.scrape_field_offices()
        scraper = ICEGovFacilityScraper(field_offices)
        facilities_data = scraper.scrape_facilities()
    elif args.load_existing:
        facilities_data = copy.deepcopy(default_data.facilities_data)
        logger.info(
            "Loaded %s existing facilities from local data. (Not scraping)",
            len(facilities_data["facilities"].keys()),  # type: ignore [attr-defined]
        )

    if args.enrich:
        if not facilities_data:
            logger.warning("No facility data available for enrichment.")
            return
        enricher = ExternalDataEnricher()
        facilities_data = enricher.enrich_facility_data(facilities_data)

    if facilities_data:
        output_filename = args.output_file_name
        if args.enrich and not output_filename.endswith("_enriched"):
            output_filename = f"{output_filename}_enriched"
        export_to_file(facilities_data, output_filename, args.file_type)
        print_summary(facilities_data)
    else:
        logger.warning("No data to export!")


if __name__ == "__main__":
    main()
