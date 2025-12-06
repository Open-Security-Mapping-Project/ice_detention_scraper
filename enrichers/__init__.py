"""
Import order here is a touch weird, but we need it so
types exist before attempting to import functions that
may call them
"""

import copy
from schemas import enrich_resp_schema


class Enrichment(object):
    _required_keys = [
        "facility_name",
    ]

    def __init__(self, **kwargs):
        self.resp_info = copy.deepcopy(enrich_resp_schema)
        for k in self._required_keys:
            if k not in kwargs.keys():
                raise KeyError("Missing required key %s in %s", k, kwargs)
        self.search_args = copy.deepcopy(kwargs)

    def search(self) -> dict:
        """Child objects should implement this"""
        return {}

    def _minimal_clean_facility_name(self, name: str) -> str:
        """Minimal cleaning that preserves important context like 'County Jail'"""
        cleaned = name

        # Remove pipe separators and take the main name
        if "|" in cleaned:
            parts = cleaned.split("|")
            cleaned = max(parts, key=len).strip()

        # Only remove very generic suffixes, keep specific ones like "County Jail"
        generic_suffixes = [
            "Service Processing Center",
            "ICE Processing Center",
            "Immigration Processing Center",
            "Contract Detention Facility",
            "Adult Detention Facility",
        ]

        for suffix in generic_suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()
                break

        return cleaned

    def _clean_facility_name(self, name: str) -> str:
        """Clean facility name for better search results"""
        # Remove common suffixes and prefixes that might interfere with search
        # This function may not be helpful - may be counterproductive.
        cleaned = name

        # Remove pipe separators and take the main name
        if "|" in cleaned:
            parts = cleaned.split("|")
            # Take the longer part as it's likely the full name
            cleaned = max(parts, key=len).strip()

        # Remove common facility type suffixes for broader search
        suffixes_to_remove = [
            "Detention Center",
            "Processing Center",
            "Correctional Center",
            "Correctional Facility",
            "Detention Facility",
            "Service Processing Center",
            "ICE Processing Center",
            "Immigration Processing Center",
            "Adult Detention Facility",
            "Contract Detention Facility",
            "Regional Detention Center",
            "County Jail",
            "County Detention Center",
            "Sheriff's Office",
            "Justice Center",
            "Safety Center",
            "Jail Services",
            "Correctional Complex",
            "Public Safety Complex",
        ]

        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()
                break
        return cleaned


from .general import enrich_facility_data  # noqa: F401,E402
