import copy

"""
Handle manually discovered/managed facilities
"""
custom_facilities: dict = {
    "2309 North Highway 83,McCook,NE,69001": {
        "_repaired_record": False,
        "address": {
            "administrative_area": "NE",
            "country": "United States",
            "locality": "McCook",
            "postal_code": "69001",
            "street": "2309 North Highway 83",
        },
        "address_str": "North Highway 83,McCook,NE,69001",
        "facility_type": {
            "expanded_name": "Pending Classification and Inclusion",
            "description": "Facilities discovered through other means that may become ICE/DHS facilities",
            "id": "Pending",
        },
        "field_office": {
            "address": {
                "administrative_area": "MN",
                "country": "United States",
                "locality": "Fort Snelling",
                "postal_code": "55111",
                "street": "1 Federal Drive Suite 1601",
            },
            "address_str": "1 Federal Drive Suite 1601 Fort Snelling, MN 55111",
            "aor": "Iowa, Minnesota, Nebraska, North Dakota, South Dakota",
            "email": "StPaul.Outreach@ice.dhs.gov",
            "field_office": "St Paul Field Office",
            "id": "SPM",
            "name": "Fort Snelling - ERO",
            "phone": "(612) 843-8600",
            "source_urls": ["https://www.ice.gov/contact/field-offices?page=2&exposed_form_display=1"],
        },
        "image_url": "https://corrections.nebraska.gov/sites/default/files/2024-08/wec_thumbnail.jpg",
        "inspection": {
            "last_date": None,
            "last_rating": "",
            "last_type": "",
        },
        "name": "Work Ethic Camp",
        "osm": {
            "latitude": 40.22851,
            "longitude": -100.548001,
            "search_query": "",
            "url": "https://www.openstreetmap.org/way/456014773#map=19/40.228251/-100.648001",
        },
        "page_updated_date": None,
        "phone": "308-345-8405",
        "population": {
            "female": {"allowed": False, "criminal": 0, "non_criminal": 0},
            "avg_stay_length": 0,
            "ice_threat_level": {
                "level_1": 0,
                "level_2": 0,
                "level_3": 0,
                "none": 0,
            },
            "male": {"allowed": False, "criminal": 0, "non_criminal": 0},
            "housing": {"guaranteed_min": 0, "mandatory": 0},
            "security_threat": {
                "high": 0,
                "low": 0,
                "medium_high": 0,
                "medium_low": 0,
            },
            "total": 0,
        },
        "source_urls": [
            "https://corrections.nebraska.gov/facilities/work-ethic-camp",
        ],
        "wikidata": {"page_url": "", "search_query": ""},
        "wikipedia": {"page_url": "", "search_query": ""},
    },
}


def insert_additional_facilities(facilities_data: dict) -> dict:
    for facility_id, facility in custom_facilities.items():
        facilities_data["facilities"][facility_id] = copy.deepcopy(facility)
    return facilities_data
