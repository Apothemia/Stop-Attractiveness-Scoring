import math
from collections import defaultdict
from typing import Iterable, Mapping, Any


def _geo_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _minmax_norm(values_by_key: Mapping[str, float]) -> dict[str, float]:
    if not values_by_key:
        return {}
    vals = list(values_by_key.values())
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        return {k: 0.0 for k in values_by_key}
    return {k: (v - vmin) / (vmax - vmin) for k, v in values_by_key.items()}


def _stations_latlon_by_abbr() -> dict[str, tuple[float, float]]:
    """
    Returns {Stations.abbreviation: (latitude, longitude)}.

    IMPORTANT: YearlyUsage.source/destination are 4-letter station abbreviations,
    so we must match them against Stations.abbreviation (NOT Stations.code).
    """
    from .models import Stations  # local import avoids import-cycle issues

    return {
        s["abbreviation"]: (float(s["latitude"]), float(s["longitude"]))
        for s in Stations.objects.all().values("abbreviation", "latitude", "longitude")
    }


def station_attractiveness_scores_from_filtered_records(
        *,
        records: Iterable[Mapping[str, Any]],
        stations_latlon_by_abbr: Mapping[str, tuple[float, float]] | None = None,
        weights: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> dict[str, dict[str, float]]:
    """
    Computes station scores using ONLY the provided (already UI-filtered) OD records.

    Inputs
    - records: iterable of dict-like rows containing at least:
        { "source": str, "destination": str, "passengers": int }
    - stations_latlon_by_abbr:
        mapping "ABBR" -> (lat, lon).
        If None, it will be loaded from Stations.abbreviation/latitude/longitude.
    - weights: (w1, w2, w3) for (Board, EffDst, Access)

    Output
    - dict keyed by station abbreviation, with:
        {
          "board": float in [0,1],
          "eff_dst": float in [0,1],
          "access": float in [0,1],
          "as": float (weighted sum, typically in [0, sum(weights)]),
          "raw_boardings": float,
          "raw_eff_dst": float,
          "raw_access": float,
        }
    """
    w1, w2, w3 = weights

    if stations_latlon_by_abbr is None:
        stations_latlon_by_abbr = _stations_latlon_by_abbr()

    # Aggregate from filtered records
    boardings_by_src = defaultdict(float)  # B_i
    inbound_by_dst = defaultdict(float)  # A_j
    flow_by_src_dst = defaultdict(lambda: defaultdict(float))  # F_ij

    for r in records:
        src = r.get("source")
        dst = r.get("destination")
        p = float(r.get("passengers") or 0)

        if not src or not dst or p <= 0:
            continue
        if src == dst:
            continue

        boardings_by_src[src] += p
        inbound_by_dst[dst] += p
        flow_by_src_dst[src][dst] += p

    # Data validation (scope limited to UI-filtered records AND stations we can locate by abbreviation)
    stations_in_scope = {
        abbr for abbr in set(boardings_by_src) | set(inbound_by_dst) | set(flow_by_src_dst)
        if abbr in stations_latlon_by_abbr
    }
    if not stations_in_scope:
        return {}

    # EffDst
    raw_effdst_by_src: dict[str, float] = {}
    for src in stations_in_scope:
        flows = flow_by_src_dst.get(src, {})
        total = sum(flows.values())
        if total <= 0:
            raw_effdst_by_src[src] = 0.0
            continue

        # Shannon entropy H_i = -sum p_ij ln(p_ij), D_i = exp(H_i)
        H = 0.0
        for f in flows.values():
            pij = f / total
            if pij > 0:
                H -= pij * math.log(pij)
        raw_effdst_by_src[src] = math.exp(H)

    # Access
    raw_access_by_src: dict[str, float] = {}
    for src in stations_in_scope:
        src_latlon = stations_latlon_by_abbr.get(src)
        if not src_latlon:
            raw_access_by_src[src] = 0.0
            continue
        src_lat, src_lon = src_latlon

        acc = 0.0
        for dst, Aj in inbound_by_dst.items():
            if dst == src:
                continue
            dst_latlon = stations_latlon_by_abbr.get(dst)
            if not dst_latlon:
                continue
            dst_lat, dst_lon = dst_latlon

            dist_km = _geo_distance(src_lat, src_lon, dst_lat, dst_lon)
            decay = 1.0 / (1.0 + dist_km)  # f(dist) = 1 / (1 + dist)
            acc += float(Aj) * decay

        raw_access_by_src[src] = acc

    # Min-Max normalisation to [0,1] (within filtered scope)
    raw_boardings_by_src = {k: float(v) for k, v in boardings_by_src.items() if k in stations_in_scope}
    board_norm = _minmax_norm(raw_boardings_by_src)
    effdst_norm = _minmax_norm({k: raw_effdst_by_src[k] for k in stations_in_scope})
    access_norm = _minmax_norm({k: raw_access_by_src[k] for k in stations_in_scope})

    out: dict[str, dict[str, float]] = {}
    for s in stations_in_scope:
        b = board_norm.get(s, 0.0)
        d = effdst_norm.get(s, 0.0)
        a = access_norm.get(s, 0.0)
        out[s] = {
            "board": b,
            "eff_dst": d,
            "access": a,
            "as": (w1 * b) + (w2 * d) + (w3 * a),
            "raw_boardings": raw_boardings_by_src.get(s, 0.0),
            "raw_eff_dst": raw_effdst_by_src.get(s, 0.0),
            "raw_access": raw_access_by_src.get(s, 0.0),
        }
    return out
