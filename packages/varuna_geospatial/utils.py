"""VARUNA GRID — coordinate math. WGS84 lon/lat, kilometres, UTC."""

from __future__ import annotations

import numpy as np

from varuna_contracts.schemas import BBox, GeoPoint

EARTH_RADIUS_KM = 6371.0088
DEG_LAT_KM = 111.32


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in km between two points."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlam / 2) ** 2
    return float(2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a)))


def haversine_km_vec(
    lon1: np.ndarray, lat1: np.ndarray, lon2: float, lat2: float
) -> np.ndarray:
    """Vectorised distance from many points to one. Use this in hot loops."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def km_to_deg_lat(km: float) -> float:
    return km / DEG_LAT_KM


def km_to_deg_lon(km: float, at_lat: float) -> float:
    return km / (DEG_LAT_KM * max(np.cos(np.radians(at_lat)), 0.01))


def expand_bbox(box: BBox, km: float) -> BBox:
    """Grow a bbox by `km` on all sides, clamped to valid ranges."""
    dlat = km_to_deg_lat(km)
    dlon = km_to_deg_lon(km, box.center.lat)
    return BBox(
        min_lon=max(-180.0, box.min_lon - dlon),
        min_lat=max(-90.0, box.min_lat - dlat),
        max_lon=min(180.0, box.max_lon + dlon),
        max_lat=min(90.0, box.max_lat + dlat),
    )


def bbox_from_points(lons: np.ndarray, lats: np.ndarray, pad_km: float = 0.0) -> BBox:
    box = BBox(
        min_lon=float(np.min(lons)), min_lat=float(np.min(lats)),
        max_lon=float(np.max(lons)), max_lat=float(np.max(lats)),
    )
    return expand_bbox(box, pad_km) if pad_km else box


def bbox_area_km2(box: BBox) -> float:
    h = (box.max_lat - box.min_lat) * DEG_LAT_KM
    w = (box.max_lon - box.min_lon) * DEG_LAT_KM * np.cos(np.radians(box.center.lat))
    return float(abs(h * w))


def destination_point(
    lon: float, lat: float, bearing_deg: float, distance_km: float
) -> GeoPoint:
    """Point at `distance_km` along `bearing_deg` from origin."""
    br = np.radians(bearing_deg)
    d = distance_km / EARTH_RADIUS_KM
    p1, l1 = np.radians(lat), np.radians(lon)
    p2 = np.arcsin(np.sin(p1) * np.cos(d) + np.cos(p1) * np.sin(d) * np.cos(br))
    l2 = l1 + np.arctan2(
        np.sin(br) * np.sin(d) * np.cos(p1), np.cos(d) - np.sin(p1) * np.sin(p2)
    )
    return GeoPoint(lon=float((np.degrees(l2) + 540) % 360 - 180), lat=float(np.degrees(p2)))


def point_to_segment_km(
    plon: float, plat: float,
    alon: float, alat: float, blon: float, blat: float,
) -> float:
    """Distance from a point to a line segment, in a local flat approximation."""
    cos_lat = max(np.cos(np.radians(plat)), 0.01)
    px, py = plon * cos_lat * DEG_LAT_KM, plat * DEG_LAT_KM
    ax, ay = alon * cos_lat * DEG_LAT_KM, alat * DEG_LAT_KM
    bx, by = blon * cos_lat * DEG_LAT_KM, blat * DEG_LAT_KM
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 == 0.0:
        return float(np.hypot(px - ax, py - ay))
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg2))
    return float(np.hypot(px - (ax + t * dx), py - (ay + t * dy)))
