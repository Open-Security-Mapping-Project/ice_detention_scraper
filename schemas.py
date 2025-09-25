import copy
import datetime

facilities_schema = {
    "enrich_runtime": 0,
    "facilities": {},
    "scrape_runtime": 0,
    "scraped_date": datetime.datetime.now(datetime.UTC),
}

field_offices_schema: dict = {
    "field_offices": {},
    "scrape_runtime": 0,
    "scraped_date": datetime.datetime.now(datetime.UTC),
}

field_office_schema: dict = {
    "address": {
        "administrative_area": "",
        "country": "",
        "locality": "",
        "postal_code": "",
        "street": "",
    },
    "address_str": "",
    "aor": "",
    "email": "",
    "field_office": "",
    "id": "",
    "name": "",
    "source_urls": [],
}

# default keys to "false"-y values so we can merge easier
facility_schema: dict = {
    "_repaired_record": False,
    "address": {
        "administrative_area": "",
        "country": "",
        "locality": "",
        "postal_code": "",
        "street": "",
    },
    "address_str": "",
    "field_office": copy.deepcopy(field_office_schema),
    "facility_type": {
        "description": "",
        "expanded_name": "",
        "id": "",
    },
    "inspection": {
        "last_date": None,
        "last_rating": "",
        "last_type": "",
    },
    "image_url": "",
    "osm": {
        "latitude": 0,
        "longitude": 0,
        "search_query": "",
        "url": "",
    },
    "name": "",
    "page_updated_date": None,
    "phone": "",
    "population": {
        "avg_stay_length": 0,
        "female": {
            "allowed": False,
            "criminal": 0,
            "non_criminal": 0,
        },
        "male": {
            "allowed": False,
            "criminal": 0,
            "non_criminal": 0,
        },
        "housing": {
            "mandatory": 0,
            "guaranteed_min": 0,
        },
        "ice_threat_level": {
            "level_1": 0,
            "level_2": 0,
            "level_3": 0,
            "none": 0,
        },
        "security_threat": {
            "low": 0,
            "medium_low": 0,
            "medium_high": 0,
            "high": 0,
        },
        "total": 0,
    },
    "source_urls": [],
    "vera_id": "",
    "wikipedia": {
        "page_url": "",
        "search_query": "",
    },
    "wikidata": {
        "page_url": "",
        "search_query": "",
    },
}


# enrichment response object
enrich_resp_schema = {
    "cleaned_name": "",
    "details": {},
    "enrichment_type": "",
    "method": "none",
    "original_name": "",
    "search_query_steps": [],
    "url": "",
}

# enrichment print details
enrichment_print_schema = {
    "osm_found": 0,
    "wiki_found": 0,
    "wikidata_found": 0,
}

supported_output_types = ["csv", "json", "parquet", "xlsx"]
