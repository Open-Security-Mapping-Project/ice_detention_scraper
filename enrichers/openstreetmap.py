from schemas import default_coords
from enrichers import Enrichment
from utils import logger


class OpenStreetMap(Enrichment):
    def search(self) -> dict:
        facility_name = self.search_args["facility_name"]
        address = self.search_args.get("address", {})
        search_name = self._clean_facility_name(facility_name)
        search_url = "https://nominatim.openstreetmap.org/search"
        self.resp_info["enrichment_type"] = "openstreetmap"
        data = []
        if not address:
            logger.debug("No address for %s, simply searching for name", facility_name)
            params = {
                "q": search_name,
                "format": "json",
                "limit": 5,
                "dedupe": 1,
            }
            logger.debug("Searching OSM for %s", search_name)
            self.resp_info["search_query_steps"].append(search_name)  # type: ignore [attr-defined]
            try:
                response = self._req(search_url, params=params, timeout=15)
                logger.debug("Response: %s", response.text)
                data = response.json()
            except Exception as e:
                logger.debug(" OSM search error for '%s': %s", facility_name, e)
                self.resp_info["search_query_steps"].append(f"(Failed -> {e})")  # type: ignore [attr-defined]
                return self.resp_info
        else:
            full_address = (
                f"{address['street']} {address['locality']}, {address['administrative_area']} {address['postal_code']}"
            )
            locality = f"{address['locality']}, {address['administrative_area']} {address['postal_code']}"
            search_url = "https://nominatim.openstreetmap.org/search"
            search_params = {
                "facility_name": {
                    "q": f"{search_name} {full_address}",
                    "format": "json",
                    "limit": 5,
                    "dedupe": 1,
                },
                "street_address": {
                    "q": f"{full_address}",
                    "format": "json",
                    "limit": 5,
                    "dedupe": 1,
                },
                "locality": {
                    "q": f"{locality}",
                    "format": "json",
                    "limit": 5,
                    "dedupe": 1,
                },
            }
            for search_name, params in search_params.items():
                logger.debug("Searching OSM for %s", params["q"])
                self.resp_info["search_query_steps"].append(params["q"])  # type: ignore [attr-defined]
                try:
                    response = self._req(search_url, params=params, timeout=15)
                    data = response.json()
                except Exception as e:
                    logger.debug(" OSM search error for '%s': %s", facility_name, e)
                    self.resp_info["search_query_steps"].append(f"(Failed -> {e})")  # type: ignore [attr-defined]
                    continue
                if data:
                    return self.resp_info
        # when the URL result is a "way" this is usually correct.
        # checks top five results.
        match_terms = ["prison", "detention", "correctional", "jail"]
        for result in data:
            osm_type = result.get("type", "").lower()
            lat = result.get("lat", default_coords["latitude"])
            lon = result.get("lon", default_coords["longitude"])
            display_name = result.get("display_name", "").lower()
            if any(term in osm_type for term in match_terms) or any(term in display_name for term in match_terms):
                # todo courthouse could be added, or other tags such as "prison:for=migrant" as a clear positive search result.
                osm_id = result.get("osm_id", "")
                osm_type_prefix = result.get("osm_type", "")
                title = result.get("display_name", "")
                if osm_id and osm_type_prefix:
                    self.resp_info["url"] = f"https://www.openstreetmap.org/{osm_type_prefix}/{osm_id}"
                    self.resp_info["details"]["latitude"] = lat  # type: ignore [index]
                    self.resp_info["details"]["longitude"] = lon  # type: ignore [index]
                    self.resp_info["title"] = title
                    return self.resp_info
        # fallback to first result
        first_result = data[0]
        logger.debug("Address searches didn't directly find anything, just using the first result: %s", first_result)
        title = first_result.get("display_name", "")
        lat = first_result.get("lat", default_coords["latitude"])
        lon = first_result.get("lon", default_coords["longitude"])
        self.resp_info["search_query_steps"].append(f"{lat}&{lon}")  # type: ignore [attr-defined]
        if lat and lon:
            self.resp_info["url"] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15"
            self.resp_info["details"]["latitude"] = lat  # type: ignore [index]
            self.resp_info["details"]["longitude"] = lon  # type: ignore [index]
            self.resp_info["title"] = title
        return self.resp_info
