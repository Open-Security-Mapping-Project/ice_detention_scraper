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
    python main.py --load-existing --enrich --debug -o debug_facilities
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import copy
import logging
from file_utils import export_to_file, print_summary
import default_data
from ice_scrapers import facilities_scrape_wrapper
from enrichers import enrich_facility_data
from schemas import supported_output_types
from utils import logger


def main() -> None:
    parser = ArgumentParser(
        description="ICE Detention Facilities Data Scraper and Enricher",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    _ = parser.add_argument(
        "--scrape",
        action="store_true",
        default=False,
        help="Scrape initial facility data from ICE.gov",
    )
    _ = parser.add_argument(
        "--enrich",
        action="store_true",
        default=False,
        help="enrich collected data",
    )
    _ = parser.add_argument(
        "--load-existing",
        action="store_true",
        default=False,
        help="load data from local files",
    )
    _ = parser.add_argument(
        "--file-type",
        choices=supported_output_types,
        type=str,
        default="csv",
        help="type of file to export",
    )
    _ = parser.add_argument(
        "--output-file-name",
        "-o",
        default="ice_detention_facilities",
        type=str,
        help="The file we'll write data out to (excluding the suffix)",
    )
    _ = parser.add_argument(
        "--debug",
        action="store_true",
        help="Full debug information and logging",
    )
    _ = parser.add_argument(
        "--enrich-workers",
        type=int,
        default=3,
        help="Number of concurrent processes to allow while enriching data",
    )
    # todo these need more attention, but should now be accepted as command line options now.
    _ = parser.add_argument(
        "--debug-wikipedia",
        action="store_true",
        help="Add another column on export for Wikipedia debugging details and redirects",
    )
    _ = parser.add_argument(
        "--debug-wikidata",
        action="store_true",
        help="Add another column on export for Wikidata debugging details and redirects",
    )
    _ = parser.add_argument(
        "--debug-osm",
        action="store_true",
        help="Add another column on export for OpenStreetMap debugging details and redirects",
    )
    _ = parser.add_argument(
        "--skip-downloads",
        action="store_true",
        help="Skip downloading sheet data",
    )
    _ = parser.add_argument(
        "--delete-sheets",
        action="store_true",
        help="Remove any sheets we downloaded",
    )
    _ = parser.add_argument(
        "--use-vera",
        action="store_true",
        default=False,
        help="Collect vera.org data",
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
            "  Warning: --debug-wikipedia, --debug-wikidata and --debug-osm are currently not implemented as command line options."
        )
    if args.scrape and args.load_existing:
        logger.error("Can't scrape and load existing data!")
        exit(1)

    facilities_data: dict = {}
    if args.scrape:
        facilities_data, agencies = facilities_scrape_wrapper(
            keep_sheet=not args.delete_sheets,
            force_download=not args.skip_downloads,
            skip_vera=not args.use_vera,
        )
    elif args.load_existing:
        facilities_data = copy.deepcopy(default_data.facilities_data)
        logger.info(
            "Loaded %s existing facilities from local data. (Not scraping)",
            len(facilities_data["facilities"].keys()),  # type: ignore [attr-defined]
        )
    elif args.enrich:
        facilities_data = copy.deepcopy(default_data.facilities_data)
        logger.warning(
            "  Did not supply --scrape or --load-existing. Proceeding with default data set (%s facilities)",
            len(facilities_data["facilities"].keys()),  # type: ignore [attr-defined]
        )

    if args.enrich:
        if not facilities_data:
            logger.warning("  No facility data available for enrichment.")
            return
        facilities_data = enrich_facility_data(facilities_data, args.enrich_workers)

    if facilities_data:
        output_filename = args.output_file_name
        if args.enrich and not output_filename.endswith("_enriched"):
            output_filename = f"{output_filename}_enriched"
        if not args.file_type:
            for ftype in supported_output_types:
                export_to_file(facilities_data, output_filename, ftype)
        else:
            export_to_file(facilities_data, output_filename, args.file_type)
        print_summary(facilities_data)
    else:
        logger.warning("  No data to export!")


if __name__ == "__main__":
    main()
