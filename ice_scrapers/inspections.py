from bs4 import BeautifulSoup
import copy
import os
import pdfplumber
from pprint import pformat
import re
from schemas import inspection_schema
import sys
from utils import (
    logger,
    output_folder,
    req_get,
)
import zstandard as zstd

from .utils import download_file

root_url = "https://www.ice.gov/foia/odo-facility-inspections"
storage_dir = f"{output_folder}{os.sep}inspections{os.sep}"
"""
example: 2011 Calhoun County Correctional Facility, Battle Creek, MI - Dec. 6-8, 2011
example 2: 2024 Chippewa County, Sault Sainte Marie, MI – Apr. 23-25, 2024
example 3: FY 2018 South Texas ICE Processing Center Compliance Inspection Report – Pearsall, TX - May 1-3, 2018
"""
text_re = re.compile(r"^(\w+\s)?(\d+)\s(.+)\s(-|–)\s(.+)$")


def _extract_txt(url: str) -> str:
    file_name = url.split("/")[-1]  # type: ignore [union-attr]
    download_file(str(url), f"{storage_dir}{file_name}")
    full_text = ""
    with pdfplumber.open(f"{storage_dir}{file_name}") as pdf:
        for idx, page in enumerate(pdf.pages):
            txt = page.extract_text()
            logger.debug("    Page %s: %s", idx + 1, txt)
            full_text = f"{full_text}\n{txt}"
    return full_text


def find_inspections(keep_text: bool = True) -> dict:
    os.makedirs(storage_dir, exist_ok=True)
    inspections: dict = {}
    logger.info("Collecting inspection reports from %s", root_url)
    resp = req_get(root_url, timeout=120)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    content = soup.select_one("div.facility-inspections")
    links = content.select("a")  # type: ignore [union-attr]
    for link in links:
        url = link["href"]
        obj = copy.deepcopy(inspection_schema)
        matches = text_re.search(link.text.strip())
        if len(matches.groups()) < 5:  # type: ignore [union-attr]
            logger.warning("  Did not find all expected groups in %s. Skipping...", link.text.strip())
            continue
        # third capture group should be the facility name
        location: str = matches.group(3)  # type: ignore [union-attr]
        # fifth capture group should be the inspection date
        date: str = matches.group(5)  # type: ignore [union-attr]
        obj["date"] = date
        if keep_text:
            text = zstd.compress(_extract_txt(str(url)).encode("utf-8"))
            logger.debug(
                "    Facility: %s, date: %s, url: %s, report length (compressed): %s",
                location,
                date,
                url,
                sys.getsizeof(text),
            )
            obj["text"] = text
        if location in inspections:
            inspections[location].append(obj)
        else:
            inspections[location] = [obj]
    logger.debug(pformat(inspections))
    return inspections
