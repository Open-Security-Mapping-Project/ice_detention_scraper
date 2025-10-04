"""
Import order here is a touch weird, but we need it so
types exist before attempting to import functions that
may call them
"""

ice_inspection_types = {
    # found in https://www.ice.gov/foia/odo-facility-inspections
    "ODO": "Office of Detention Oversight",
    # found in https://ia803100.us.archive.org/16/items/6213032-ORSA-MOU-ICE/6213032-ORSA-MOU-ICE_text.pdf
    "ORSA": "Operational Review Self-Assessment",
}

# extracted from https://vera-institute.files.svdcdn.com/production/downloads/dashboard_appendix.pdf 2025-09-23
ice_facility_group_mapping = {
    "Non-Dedicated": ["IGSA"],
    "Dedicated": ["DIGSA", "CDF", "SPC"],
    "Federal": ["BOF", "USMSIGA", "USMS IGA", "USMS CDF", "DOD", "MOC"],
    "Hold/Staging": ["Hold", "Staging"],
    "Family/Youth": ["Family", "Juvenile", "FAMILY"],
    "Medical": ["Hospital"],
    "Hotel": ["Hotel"],
    "Other/Unknown": ["Other", "Unknown", "Pending"],
}

# extracted from https://www.ice.gov/doclib/detention/FY25_detentionStats08292025.xlsx 2025-09-07
# and https://vera-institute.files.svdcdn.com/production/downloads/dashboard_appendix.pdf 2025-09-23
ice_facility_types = {
    "BOP": {
        "expanded_name": "Federal Bureau of Prisons",
        "description": "A facility operated by the Federal Bureau of Prisons",
    },
    "CDF": {
        "expanded_name": "Contract Detention Facility",
        "description": "Name derived from listing at https://www.vera.org/ice-detention-trends",
    },
    "DIGSA": {
        "expanded_name": "Dedicated Intergovernmental Service Agreement",
        "description": "A publicly-owned facility operated by state/local government(s), or private contractors, in which ICE contracts to use all bed space via a Dedicated Intergovernmental Service Agreement; or facilities used by ICE pursuant to Intergovernmental Service Agreements, which house only ICE detainees – typically these are operated by private contractors pursuant to their agreements with local governments.",
    },
    "DOD": {
        "expanded_name": "Department of Defence",
        "description": "Department of Defence facilities - Often Army bases",
    },
    "FAMILY": {
        "expanded_name": "Family",
        "description": "A facility in which families are able to remain together while awaiting their proceedings",
    },
    "Family": {
        "expanded_name": "Family",
        "description": "A facility in which families are able to remain together while awaiting their proceedings",
    },
    "Hospital": {
        "expanded_name": "Hospital",
        "description": "A medical facility",
    },
    "IGSA": {
        "expanded_name": "Intergovernmental Service Agreement",
        "description": "A publicly-owned facility operated by state/local government(s), or private contractors, in which ICE contracts for bed space via an Intergovernmental Service Agreement; or local jails used by ICE pursuant to Intergovernmental Service Agreements, which house both ICE and non-ICE detainees, typically county prisoners awaiting trial or serving short sentences, but sometimes also USMS prisoners.",
    },
    "Juvenile": {
        "expanded_name": "Juvenile",
        "description": "An IGSA facility capable of housing juveniles (separate from adults) for a temporary period of time",
    },
    "Other": {
        "expanded_name": "Other",
        "description": "Facilities including but not limited to transportation-related facilities, hotels, and/or other facilities",
    },
    "Unknown": {
        "expanded_name": "Unknown",
        "description": "A facility whose type could not be identified",
    },
    "SPC": {
        "expanded_name": "Service Processing Center",
        "description": "A facility owned by the government and staffed by a combination of federal and contract employees.",
    },
    "USMS": {
        "expanded_name": "United States Marshals Service",
        "description": "A facility primarily contracted with the USMS for housing of USMS detainees, in which ICE contracts with the USMS for bed space.",
    },
    # two keys for the same thing as it isn't consistently defined
    "USMSIGA": {
        "expanded_name": "United States Marshals Service Intergovernmental Agreement",
        "description": "A USMS Intergovernmental Agreement in which ICE agrees to utilize an already established US Marshals Service contract.",
    },
    "USMS IGA": {
        "expanded_name": "United States Marshals Service Intergovernmental Agreement",
        "description": "A USMS Intergovernmental Agreement in which ICE agrees to utilize an already established US Marshals Service contract.",
    },
    "USMS CDF": {
        "expanded_name": "United States Marshals Service Contract Detention Facility",
        "description": "Name derived from listing at https://www.vera.org/ice-detention-trends",
    },
    "Staging": {
        "description": "Some facilities in the ICE spreadsheet are marked 'Staging'. Hard to determine why.",
        "expanded_name": "Staging",
    },
    "Pending": {
        "expanded_name": "Pending Classication and Inclusion",
        "description": "Facilities discovered through other means that may become ICE/DHS facilities",
    },
}

# ICE AOR mappings
area_of_responsibility = {
    "ATL": "Atlanta Field Office",
    "BAL": "Baltimore Field Office",
    "BOS": "Boston Field Office",
    "BUF": "Buffalo Field Office",
    "CHI": "Chicago Field Office",
    "DAL": "Dallas Field Office",
    "DEN": "Denver Field Office",
    "DET": "Detroit Field Office",
    "ELP": "El Paso Field Office",
    "HLG": "Harlingen Field Office",
    "HOU": "Houston Field Office",
    "LOS": "Los Angeles Field Office",
    "MIA": "Miami Field Office",
    "NEW": "Newark Field Office",
    "NOL": "New Orleans Field Office",
    "NYC": "New York City Field Office",
    "PHI": "Philadelphia Field Office",
    "PHO": "Phoenix Field Office",
    "SEA": "Seattle Field Office",
    "SFR": "San Francisco Field Office",
    "SLC": "Salt Lake City Field Office",
    "SNA": "San Antonio Field Office",
    "SND": "San Diego Field Office",
    "SPM": "St Paul Field Office",
    "WAS": "Washington Field Office",
}
field_office_to_aor = {v: k for k, v in area_of_responsibility.items()}

from .utils import (  # noqa: E402
    get_ice_scrape_pages,  # noqa: F401
    repair_locality,  # noqa: F401
    repair_name,  # noqa: F401
    repair_street,  # noqa: F401
    repair_zip,  # noqa: F401
    special_facilities,  # noqa: F401
    update_facility,  # noqa: F401
)
from .facilities_scraper import scrape_facilities  # noqa: F401,E402
from .spreadsheet_load import load_sheet  # noqa: F401,E402
from .field_offices import (  # noqa: E402
    merge_field_offices,  # noqa: F401
    scrape_field_offices,  # noqa: F401
)
from .vera_data import collect_vera_facility_data  # noqa: F401,E402
from .custom_facilities import insert_additional_facilities  # noqa: F401,E402
from .general import facilities_scrape_wrapper  # noqa: F401,E402
