"""Build a Plotly map (OpenStreetMap) for the destination city + training-related places."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
import plotly.graph_objects as go


async def _geocode(city: str, country_code: str = "") -> dict[str, Any] | None:
    key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not key:
        return None
    q = f"{city},{country_code}" if country_code else city
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": q, "limit": 1, "appid": key},
        )
    if r.status_code != 200:
        return None
    data = r.json()
    if not data:
        return None
    loc = data[0]
    return {"lat": loc.get("lat"), "lon": loc.get("lon"), "name": loc.get("name")}


async def _places_nearby(
    query: str,
    lat: float,
    lon: float,
) -> list[dict[str, Any]]:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        return []
    params: dict[str, Any] = {
        "query": query,
        "key": key,
        "location": f"{lat},{lon}",
        "radius": 12000,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
        )
    data = r.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        return []
    out = []
    for p in (data.get("results") or [])[:12]:
        loc = p.get("geometry", {}).get("location", {})
        la, ln = loc.get("lat"), loc.get("lng")
        if la is None or ln is None:
            continue
        out.append(
            {
                "name": p.get("name", "Place"),
                "lat": la,
                "lon": ln,
                "address": p.get("formatted_address", ""),
            }
        )
    return out


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=message,
        height=420,
        margin=dict(l=20, r=20, t=50, b=20),
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14),
            )
        ],
    )
    return fig


async def build_destination_map(
    city: str,
    country_code: str = "",
    places_query: str = "running track gym fitness outdoor",
) -> tuple[go.Figure, str]:
    """Return (plotly figure, short status line for the UI)."""
    city = (city or "").strip()
    if not city:
        return _empty_figure("Enter a destination city to show the map."), ""

    geo = await _geocode(city, country_code)
    if not geo:
        return (
            _empty_figure(
                "Could not geocode. Set OPENWEATHERMAP_API_KEY or check the city name."
            ),
            "Map: geocoding failed (check API key / city).",
        )

    lat, lon = float(geo["lat"]), float(geo["lon"])
    places = await _places_nearby(places_query, lat, lon)

    lats = [lat]
    lons = [lon]
    texts = [f"📍 {geo.get('name', city)} (center)"]
    sizes = [16]
    colors = ["#e74c3c"]

    for p in places:
        lats.append(float(p["lat"]))
        lons.append(float(p["lon"]))
        label = p["name"]
        if p.get("address"):
            label += f"<br><span style='font-size:11px'>{p['address'][:80]}</span>"
        texts.append(label)
        sizes.append(11)
        colors.append("#2980b9")

    fig = go.Figure(
        go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode="markers",
            marker=dict(size=sizes, color=colors),
            text=texts,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=lat, lon=lon),
            zoom=13 if places else 12,
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        title=f"Training spots near {city}",
        height=440,
    )

    note = f"Map: center on **{city}**"
    if not os.environ.get("GOOGLE_MAPS_API_KEY"):
        note += " — add `GOOGLE_MAPS_API_KEY` to show nearby gyms/tracks from Places."
    elif not places:
        note += " — no Places results (try another query or radius)."
    else:
        note += f" — **{len(places)}** Places results."

    return fig, note
