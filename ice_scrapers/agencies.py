from bs4 import BeautifulSoup
import copy
import os
import polars
import re
from schemas import (
    agencies_287g,
    active_agency,
    pending_agency,
)
import time
from utils import (
    logger,
    output_folder,
    req_get,
)
from .utils import download_file

base_xlsx_url = "https://www.ice.gov/identify-and-arrest/287g"


def scrape_agencies(keep_sheet: bool = True, force_download: bool = True) -> dict:
    """Collect data on participating agencies"""
    start_time = time.time()
    resp = req_get(base_xlsx_url, timeout=120)
    soup = BeautifulSoup(resp.content, "html.parser")
    links = [link["href"] for link in soup.findAll("a", href=re.compile("^https://www.ice.gov/doclib.*xlsx"))]
    if not links:
        raise Exception(f"Could not find any XLSX files on {base_xlsx_url}")
    logger.debug(links)
    date_re = re.compile(r"\d{8}pm")
    agencies = copy.deepcopy(agencies_287g)
    for link in links:
        match link:
            case x if "participating" in x:
                schema = copy.deepcopy(active_agency)
            case x if "pending" in x:
                schema = copy.deepcopy(pending_agency)
            case _:
                raise Exception(f"Found an unsupported agency datasheet: {link}")
        """
        Yes, polars supports loading from a URL. But this pattern
        lets us cache the download
        """
        # remove the date so we can easily overwrite the local (cached) file
        filename = date_re.sub("", link.split("/")[-1])
        path = f"{output_folder}{os.sep}{filename}"
        if force_download or not os.path.exists(path):
            logger.info("Downloading agency info sheet from %s", link)
            download_file(link, path)
        df = polars.read_excel(drop_empty_rows=True, raise_if_empty=True, source=open(path, "rb"))
        for row in df.iter_rows(named=True):
            data = copy.deepcopy(schema)
            data["state"] = row["STATE"]
            data["agency"] = row["LAW ENFORCEMENT AGENCY"]
            data["county"] = row["COUNTY"]
            data["type"] = row["TYPE"]
            data["support_type"] = row["SUPPORT TYPE"]
            if "participating" in filename:
                data["moa"] = row["MOA"]
                data["signed"] = row["SIGNED"]
                data["addendum"] = row["ADDENDUM"]
                agencies["active"].append(data)
            else:
                agencies["pending"].append(data)
        if not keep_sheet:
            os.unlink(path)
    logger.info("  Collected %s active and %s pending agencies", len(agencies["active"]), len(agencies["pending"]))
    agencies["scrape_runtime"] = time.time() - start_time
    return agencies
