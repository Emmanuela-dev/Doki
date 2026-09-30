"""
Google Maps location router.

Endpoints:
  GET /location/autocomplete         place autocomplete (as user types)
  GET /location/geocode              address → lat/lng + place_id
  GET /location/reverse              lat/lng → address
  GET /location/place-detail         full detail for a place_id
"""

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.core.config import settings

router = APIRouter(prefix="/location", tags=["Location — Google Maps"])

MAPS_BASE = "https://maps.googleapis.com/maps/api"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class PlaceSuggestion(BaseModel):
    place_id: str
    description: str          # Full human-readable address/name
    main_text: str            # Primary part (e.g. business name or street)
    secondary_text: str       # Secondary part (e.g. city, country)


class GeocodeResult(BaseModel):
    place_id: str
    formatted_address: str
    lat: float
    lng: float
    county: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class PlaceDetail(BaseModel):
    place_id: str
    name: str
    formatted_address: str
    lat: float
    lng: float
    county: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    url: Optional[str] = None   # Google Maps URL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_component(components: list, *types: str) -> Optional[str]:
    """Pull a specific address component from Google's component array."""
    for comp in components:
        if any(t in comp.get("types", []) for t in types):
            return comp.get("long_name")
    return None


def _require_api_key():
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Google Maps API key is not configured. "
                   "Set GOOGLE_MAPS_API_KEY in your .env file.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/autocomplete", response_model=List[PlaceSuggestion])
async def autocomplete(
    input: str = Query(..., min_length=2, description="Partial address or place name"),
    country: str = Query("ke", description="ISO 3166-1 alpha-2 country code (default: Kenya)"),
    location_bias: Optional[str] = Query(
        None,
        description="Bias results around a lat/lng — format: 'lat,lng' e.g. '-1.286389,36.817223'",
    ),
):
    """
    Return place suggestions as the user types their location.
    Biased to Kenya by default. Integrate with a front-end location picker.
    """
    _require_api_key()

    params = {
        "input": input,
        "key": settings.GOOGLE_MAPS_API_KEY,
        "components": f"country:{country}",
        "language": "en",
    }
    if location_bias:
        params["location"] = location_bias
        params["radius"] = 50000  # 50 km radius bias

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{MAPS_BASE}/place/autocomplete/json", params=params)

    data = resp.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(status_code=502, detail=f"Google Maps error: {data.get('status')}")

    suggestions = []
    for pred in data.get("predictions", []):
        structured = pred.get("structured_formatting", {})
        suggestions.append(
            PlaceSuggestion(
                place_id=pred["place_id"],
                description=pred["description"],
                main_text=structured.get("main_text", pred["description"]),
                secondary_text=structured.get("secondary_text", ""),
            )
        )
    return suggestions


@router.get("/geocode", response_model=GeocodeResult)
async def geocode(
    address: str = Query(..., description="Full address string to geocode"),
):
    """Convert a typed address string into coordinates + place_id."""
    _require_api_key()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{MAPS_BASE}/geocode/json",
            params={"address": address, "key": settings.GOOGLE_MAPS_API_KEY, "region": "ke"},
        )

    data = resp.json()
    if data.get("status") == "ZERO_RESULTS":
        raise HTTPException(status_code=404, detail="No results found for that address")
    if data.get("status") != "OK":
        raise HTTPException(status_code=502, detail=f"Google Maps error: {data.get('status')}")

    result = data["results"][0]
    loc = result["geometry"]["location"]
    comps = result.get("address_components", [])

    return GeocodeResult(
        place_id=result["place_id"],
        formatted_address=result["formatted_address"],
        lat=loc["lat"],
        lng=loc["lng"],
        county=_extract_component(comps, "administrative_area_level_1"),
        city=_extract_component(comps, "locality", "administrative_area_level_2"),
        country=_extract_component(comps, "country"),
    )


@router.get("/reverse", response_model=GeocodeResult)
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Convert lat/lng coordinates into a human-readable address."""
    _require_api_key()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{MAPS_BASE}/geocode/json",
            params={
                "latlng": f"{lat},{lng}",
                "key": settings.GOOGLE_MAPS_API_KEY,
            },
        )

    data = resp.json()
    if data.get("status") == "ZERO_RESULTS":
        raise HTTPException(status_code=404, detail="No address found for those coordinates")
    if data.get("status") != "OK":
        raise HTTPException(status_code=502, detail=f"Google Maps error: {data.get('status')}")

    result = data["results"][0]
    loc = result["geometry"]["location"]
    comps = result.get("address_components", [])

    return GeocodeResult(
        place_id=result["place_id"],
        formatted_address=result["formatted_address"],
        lat=loc["lat"],
        lng=loc["lng"],
        county=_extract_component(comps, "administrative_area_level_1"),
        city=_extract_component(comps, "locality", "administrative_area_level_2"),
        country=_extract_component(comps, "country"),
    )


@router.get("/place-detail", response_model=PlaceDetail)
async def place_detail(
    place_id: str = Query(..., description="Google Maps place_id from autocomplete"),
):
    """
    Fetch full place details for a place_id selected from autocomplete.
    Returns the canonical address, coordinates, and county/city breakdown —
    the data you store in LocationIn when creating a listing.
    """
    _require_api_key()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{MAPS_BASE}/place/details/json",
            params={
                "place_id": place_id,
                "fields": "place_id,name,formatted_address,geometry,address_components,url",
                "key": settings.GOOGLE_MAPS_API_KEY,
            },
        )

    data = resp.json()
    if data.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Place not found")
    if data.get("status") != "OK":
        raise HTTPException(status_code=502, detail=f"Google Maps error: {data.get('status')}")

    r = data["result"]
    loc = r["geometry"]["location"]
    comps = r.get("address_components", [])

    return PlaceDetail(
        place_id=r["place_id"],
        name=r.get("name", ""),
        formatted_address=r["formatted_address"],
        lat=loc["lat"],
        lng=loc["lng"],
        county=_extract_component(comps, "administrative_area_level_1"),
        city=_extract_component(comps, "locality", "administrative_area_level_2"),
        country=_extract_component(comps, "country"),
        url=r.get("url"),
    )
