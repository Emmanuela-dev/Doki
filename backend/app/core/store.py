"""
In-memory data store — replaces the database until the DB layer is wired in.
All data lives in plain Python dicts/lists keyed by UUID strings.
"""
from typing import Dict, Any

# { listing_id: listing_dict }
listings: Dict[str, Any] = {}

# { image_id: image_dict }
listing_images: Dict[str, Any] = {}

# { transaction_id: transaction_dict }
transactions: Dict[str, Any] = {}

# { category_id: category_dict }
waste_categories: Dict[str, Any] = {
    "cat-001": {"id": "cat-001", "name": "Food Waste",         "description": "Kitchen and food processing waste"},
    "cat-002": {"id": "cat-002", "name": "Agricultural Waste", "description": "Crop residues, husks, manure"},
    "cat-003": {"id": "cat-003", "name": "Brewery Waste",      "description": "Spent grain, yeast, stillage"},
    "cat-004": {"id": "cat-004", "name": "Dairy Waste",        "description": "Whey, sludge, milk solids"},
    "cat-005": {"id": "cat-005", "name": "Sugar Factory Waste","description": "Bagasse, molasses, filter cake"},
    "cat-006": {"id": "cat-006", "name": "Coffee Husks",       "description": "Dry coffee pulp and husks"},
    "cat-007": {"id": "cat-007", "name": "Maize Residues",     "description": "Cobs, stalks, bran"},
    "cat-008": {"id": "cat-008", "name": "Hotel / Restaurant", "description": "Mixed food and organic waste"},
}

# Stub user store — real auth comes later
users: Dict[str, Any] = {
    "user-seller-001": {
        "id": "user-seller-001",
        "name": "Green Farm Ltd",
        "email": "seller@greenfarm.co.ke",
        "role": "seller",
    },
    "user-buyer-001": {
        "id": "user-buyer-001",
        "name": "BioGas Kenya",
        "email": "buyer@biogaskenya.co.ke",
        "role": "buyer",
    },
}
