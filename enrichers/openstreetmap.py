from enrichers import Enrichment
from utils import logger, req_get


class OpenStreetMap(Enrichment):
    # default to Washington, D.C.?
    default_coords: dict = {
        "latitude": 38.89511000,
        "longitude": -77.03637000,
    }

    def search(self) -> dict:
        facility_name = self.search_args["facility_name"]
        address = self.search_args.get("address", {})
        search_name = self._clean_facility_name(facility_name)
        search_url = "https://nominatim.openstreetmap.org/search"
        self.resp_info["enrichment_type"] = "openstreetmap"
        self.resp_info["method"] = "nominatim"
        data = []
        if not address:
            logger.debug("No address for %s, simply searching for name", facility_name)
            search_params = {
                "simple_name": {
                    "q": search_name,
                    "format": "json",
                    "limit": 5,
                    "dedupe": 1,
                }
            }
        else:
            full_address = (
                f"{address['street']} {address['locality']}, {address['administrative_area']} {address['postal_code']}"
            )
            locality = f"{address['locality']}, {address['administrative_area']} {address['postal_code']}"
            search_params = {
                "facility_name": {
                    "q": f"{search_name} {full_address}",
                    "format": "json",
                    "limit": 5,
                    "dedupe": 1,
                },
                "street_address": {
                    "q": full_address,
                    "format": "json",
                    "limit": 5,
                    "dedupe": 1,
                },
                "locality": {
                    "q": locality,
                    "format": "json",
                    "limit": 5,
                    "dedupe": 1,
                },
            }
        for search_name, params in search_params.items():
            logger.debug("Searching OSM for %s", params["q"])
            self.resp_info["search_query_steps"].append(params["q"])  # type: ignore [attr-defined]
            try:
                response = req_get(search_url, params=params, timeout=15)
                data.extend(response.json())
            except Exception as e:
                logger.debug(" OSM search error for '%s': %s", facility_name, e)
                self.resp_info["search_query_steps"].append(f"(Failed -> {e})")  # type: ignore [attr-defined]
                continue
            # if we find results, don't check for less accurate ones (speeds things up quite a bit)
            if data:
                break
        if not data:
            return self.resp_info
        # The first result in the list is the most detailed, so use that
        first_result = data[0]
        lat = first_result.get("lat", self.default_coords["latitude"])
        lon = first_result.get("lon", self.default_coords["longitude"])
        osm_type = first_result.get("osm_type", "")
        osm_id = first_result.get("osm_id", "")
        self.resp_info["title"] = first_result.get("display_name", "")
        self.resp_info["details"] = {"latitude": lat, "logitude": lon, "class": first_result.get("class", "")}
        if osm_type == "way":
            self.resp_info["url"] = f"https://www.openstreetmap.org/way/{osm_id}"
        else:
            self.resp_info["search_query_steps"].append(f"{lat}&{lon}")  # type: ignore [attr-defined]
            self.resp_info["url"] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}"
        return self.resp_info
