from enrichers import Enrichment
from utils import logger, req_get


class Wikidata(Enrichment):
    # wikidata can handle slightly more aggressive requests
    _wait_time = 0.5

    def search(self) -> dict:
        facility_name = self.search_args["facility_name"]
        # Fetches 3 results based on _clean_facility_name (not exact name). todo: needs adjustment.
        # Falls back to first result (usually truncated, eg. county)
        search_name_fallback = self._clean_facility_name(facility_name)
        self.resp_info["enrichment_type"] = "wikidata"
        logger.debug("Searching wikidata for %s and %s", facility_name, search_name_fallback)
        search_url = "https://www.wikidata.org/w/api.php"
        params = {
            "facility_name": {
                "action": "wbsearchentities",
                "search": facility_name,
                "language": "en",
                "format": "json",
                "limit": 3,
            },
            "fallback": {
                "action": "wbsearchentities",
                "search": search_name_fallback,
                "language": "en",
                "format": "json",
                "limit": 3,
            },
        }
        data = {}
        for search, params in params.items():
            self.resp_info["search_query_steps"].append(params["search"])  # type: ignore [attr-defined]
            try:
                response = req_get(search_url, params=params, wait_time=self._wait_time)
                data = response.json()
                break
            except Exception as e:
                logger.debug("  Wikidata search error for '%s': %s", facility_name, e)
                self.resp_info["search_query_steps"].append(f"(Failed -> {e})")  # type: ignore [attr-defined]
        if not data.get("search"):
            return self.resp_info
        match_terms = ["prison", "detention", "correctional", "jail", "facility", "processing"]
        for result in data["search"]:
            description = result.get("description", "").lower()
            if any(term in description for term in match_terms):
                self.resp_info["url"] = f"https://www.wikidata.org/wiki/{result['id']}"
                self.resp_info["title"] = result.get("label", "")
                break
        else:
            # fall back to first result
            first = data["search"][0]
            logger.debug("   Closer matching failed, falling back to first result %s", first)
            self.resp_info["url"] = f"https://www.wikidata.org/wiki/{first['id']}"
            self.resp_info["title"] = first.get("label", "")
        return self.resp_info
