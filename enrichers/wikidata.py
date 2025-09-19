from enrichers import Enrichment
from utils import logger


class Wikidata(Enrichment):
    def search(self) -> dict:
        facility_name = self.search_args["facility_name"]
        # Fetches 3 results based on _clean_facility_name (not exact name). todo: needs adjustment.
        # Falls back to first result (usually truncated, eg. county)
        search_name_fallback = self._clean_facility_name(facility_name)
        logger.debug("Searching wikidata for %s and %s", facility_name, search_name_fallback)
        search_url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": facility_name,
            "language": "en",
            "format": "json",
            "limit": 3,
        }
        self.resp_info["enrichment_type"] = "wikidata"
        data = {}
        try:
            response = self._req(search_url, params=params)
            data = response.json()
        except Exception as e:
            logger.debug("  Wikidata search error for '%s': %s", facility_name, e)
            self.resp_info["search_query_steps"].append(f"(Failed -> {e})")  # type: ignore [attr-defined]
        if not data.get("search"):
            params["search"] = search_name_fallback
            self.resp_info["search_query_steps"].append(search_name_fallback)  # type: ignore [attr-defined]
            try:
                response = self._req(search_url, params=params)
                data = response.json()
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
                return self.resp_info
        # fallback to first result
        first = data["search"][0]
        logger.debug("   Closer matching failed, falling back to first result %s", first)
        self.resp_info["url"] = f"https://www.wikidata.org/wiki/{result['id']}"
        self.resp_info["title"] = result.get("label", "")
        return self.resp_info
