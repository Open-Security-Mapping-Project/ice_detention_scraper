# For general helpers, regexes, or shared logic (e.g. phone/address parsing functions).
import logging
import os
import polars
import requests
from requests.adapters import HTTPAdapter
import time
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

output_folder = f"{SCRIPTDIR}{os.sep}output{os.sep}"
# and make sure our output folder exists
os.makedirs(output_folder, exist_ok=True)

default_timestamp = "1970-01-01T00:00:00-+0000"
timestamp_format = "%Y-%m-%dT%H:%M:%S-%z"

# all values that will only complicate workbook output types
flatdata_filtered_keys = [
    "address_str",
    "field_office.address_str",
    "osm.search_query",
    "wikipedia.search_query",
    "wikidata.search_query",
]


def req_get(url: str, **kwargs) -> requests.Response:
    """requests response wrapper to ensure we honor waits"""
    headers = kwargs.get("headers", {})
    # ensure we get all headers configured correctly
    # but manually applied headers win the argument
    for k, v in default_headers.items():
        if k in headers.keys():
            continue
        headers[k] = v

    response = session.get(
        url,
        allow_redirects=True,
        timeout=kwargs.get("timeout", 10),
        params=kwargs.get("params", {}),
        stream=kwargs.get("stream", False),
        headers=headers,
    )
    if not kwargs.get("raise_err", False):
        response.raise_for_status()
    else:
        if response.status_code > 399:
            if response.status_code < 500:
                logger.error("Client-side error in request to %s :: %s", url, response.text)
            else:
                logger.error("Server-side error in request to %s :: %s", url, response.text)
    time.sleep(kwargs.get("wait_time", 1))
    return response


def _flatdict(d: dict, parent_key: str = "", sep: str = ".", list_sep: str = ",") -> dict:
    """flatten a nested dictionary for nicer printing to workbooks (excel/csv/etc.)"""
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{str(k)}" if parent_key else str(k)
        if isinstance(v, dict):
            items.extend(_flatdict(v, new_key, sep=sep, list_sep=list_sep).items())
        elif isinstance(v, list):
            if not v:
                items.append((new_key, ""))
            elif isinstance(v[0], dict):
                for idx, value in enumerate(v):
                    items.extend(_flatdict(value, f"{new_key}{sep}{idx}", sep=sep, list_sep=list_sep).items())

            else:
                items.append((new_key, list_sep.join(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def convert_to_dataframe(d: dict) -> polars.DataFrame:
    """internal dict to dataframe"""
    flatdata = [_flatdict(f) for f in d.values()]
    """
    Ideally we'd look for the longest row to use as our schema,
    but dataframes are picky about services missing those extra rows,
    so for simpler logic, we'll just use the first row
    """
    fieldnames = [k for k in flatdata[0].keys() if k not in flatdata_filtered_keys]
    # https://docs.pola.rs/api/python/stable/reference/api/polars.from_dicts.html
    df = polars.from_dicts(
        flatdata,
        schema=fieldnames,
        schema_overrides={
            "address.postal_code": polars.Utf8,
            "field_office.address.postal_code": polars.Utf8,
        },
    )
    logger.info("Dataframe schema: %s", df.schema)
    # logger.debug("All header fields: %s", fieldnames)
    return df
