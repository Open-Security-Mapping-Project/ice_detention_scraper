# For general helpers, regexes, or shared logic (e.g. phone/address parsing functions).
import logging
import os
import polars
import requests
from requests.adapters import HTTPAdapter
import urllib3

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

_retry_strategy = urllib3.Retry(
    total=4,
    backoff_factor=1,
)
default_headers = {"User-Agent": "ICE-Facilities-Research/1.0 (Educational Research Purpose)"}
_adapter = HTTPAdapter(max_retries=_retry_strategy)
session = requests.Session()
session.mount("https://", _adapter)
session.mount("http://", _adapter)
session.headers.update(default_headers)

output_folder = f"{SCRIPTDIR}/output/"
default_timestamp = "1970-01-01T00:00:00-+0000"
timestamp_format = "%Y-%m-%dT%H:%M:%S-%z"

# all values that will only complicate workbook output types
flatdata_filtered_keys = [
    "_repaired_record",
    "address_str",
    "field_office.address_str",
    "field_office.source_urls",
    "osm.search_query",
    "source_urls",
    "wikipedia.search_query",
    "wikidata.search_query",
]


def _flatdict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """flatten a nested dictionary for nicer printing to workbooks (excel/csv/etc.)"""
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{str(k)}" if parent_key else str(k)
        if isinstance(v, dict):
            items.extend(_flatdict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def convert_to_dataframe(d: dict) -> polars.DataFrame:
    """internal dict to dataframe"""
    flatdata = [_flatdict(f) for f in d.values()]
    fieldnames = [k for k in flatdata[0].keys() if k not in flatdata_filtered_keys]
    # https://docs.pola.rs/api/python/stable/reference/api/polars.from_dicts.html
    df = polars.from_dicts(flatdata, schema=fieldnames)
    logger.debug("Dataframe: %s", df)
    logger.debug("All header fields: %s", fieldnames)
    return df
