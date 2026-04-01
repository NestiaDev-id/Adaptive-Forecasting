"""
BMKG Real-time Earthquake Scraper
=================================
Fetches earthquake data from BMKG's Nuxt payload endpoint
and saves it as clean JSON for downstream consumption.

Sources:
  - Primary: https://www.bmkg.go.id/gempabumi/gempabumi-realtime/_payload.json
  - Fallback: https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json

Usage:
  python scripts/scrape_bmkg_quakes.py
"""

import json
import os
import sys
from datetime import datetime, timezone

# Ensure project root is in path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: pip install httpx")
    sys.exit(1)

# ============================================================================
# Constants
# ============================================================================

PAYLOAD_URL = "https://www.bmkg.go.id/gempabumi/gempabumi-realtime/_payload.json"
FALLBACK_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
FALLBACK_FELT_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"

OUTPUT_DIR = os.path.join(_project_root, "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "bmkg_quakes_realtime.json")


# ============================================================================
# Nuxt Payload Parser
# ============================================================================

def _parse_nuxt_payload(raw: list) -> list[dict]:
    """
    Parse the BMKG Nuxt _payload.json format.

    The payload is a flat array where earthquake objects reference
    values by index. Each earthquake object has keys like:
      { "eventid": <idx>, "status": <idx>, "waktu": <idx>,
        "lintang": <value>, "bujur": <value>, "dalam": <value>,
        "mag": <value>, "fokal": <idx>, "area": <idx> }

    Some values are stored inline (numbers), others reference
    an index in the flat array.
    """
    # The top-level structure is: [meta, reactive, data_obj, ...]
    # data_obj contains: { "ZAqMHAzj8s": { "Infogempa": { "gempa": [idx_array] } } }
    # We need to find the gempa array.

    if not isinstance(raw, list) or len(raw) < 3:
        return []

    flat = raw  # the entire payload is a flat indexed array

    quakes = []

    # Walk the flat array looking for earthquake-shaped objects
    for item in flat:
        if not isinstance(item, dict):
            continue

        # Earthquake objects always have these keys
        if not all(k in item for k in ("eventid", "waktu", "lintang", "bujur", "dalam", "mag", "area")):
            continue

        def resolve(val):
            """Resolve a value: if it's an int index, look up in flat array."""
            if isinstance(val, int) and 0 <= val < len(flat):
                resolved = flat[val]
                # Don't resolve if the resolved value is another dict/list
                if isinstance(resolved, (str, int, float)):
                    return resolved
            return val

        try:
            eventid = resolve(item["eventid"])
            waktu = resolve(item["waktu"])
            lintang = item["lintang"]  # usually inline float
            bujur = item["bujur"]      # usually inline float
            dalam = item["dalam"]      # depth
            mag = item["mag"]          # magnitude
            area = resolve(item["area"])
            status = resolve(item.get("status", ""))
            fokal = resolve(item.get("fokal", ""))

            # Resolve nested index references for numeric fields
            if isinstance(lintang, int) and 0 <= lintang < len(flat):
                lintang = flat[lintang]
            if isinstance(bujur, int) and 0 <= bujur < len(flat):
                bujur = flat[bujur]
            if isinstance(dalam, int) and 0 <= dalam < len(flat):
                dalam = flat[dalam]
            if isinstance(mag, int) and 0 <= mag < len(flat):
                mag = flat[mag]

            quakes.append({
                "eventid": str(eventid),
                "status": str(status),
                "datetime": str(waktu),
                "latitude": float(lintang) if lintang is not None else None,
                "longitude": float(bujur) if bujur is not None else None,
                "depth_km": float(dalam) if dalam is not None else None,
                "magnitude": float(mag) if mag is not None else None,
                "focal": str(fokal),
                "area": str(area),
            })
        except (ValueError, TypeError, IndexError):
            continue

    return quakes


# ============================================================================
# Fallback Parser (data.bmkg.go.id)
# ============================================================================

def _parse_bmkg_open_data(json_data: dict) -> list[dict]:
    """Parse the official BMKG open data JSON format."""
    quakes = []
    gempa_list = json_data.get("Infogempa", {}).get("gempa", [])

    for g in gempa_list:
        try:
            # Parse coordinates from "Lintang" and "Bujur" strings
            lat_str = g.get("Lintang", "0")
            lon_str = g.get("Bujur", "0")

            # Lintang format: "3.29 LS" or "4.68 LU"
            lat = float(lat_str.replace(" LS", "").replace(" LU", ""))
            if "LS" in lat_str:
                lat = -lat

            # Bujur format: "128.72 BT"
            lon = float(lon_str.replace(" BT", "").replace(" BB", ""))

            quakes.append({
                "eventid": g.get("Eventid", ""),
                "status": "confirmed",
                "datetime": g.get("DateTime", g.get("Tanggal", "")),
                "latitude": lat,
                "longitude": lon,
                "depth_km": float(g.get("Kedalaman", "0").replace(" Km", "")),
                "magnitude": float(g.get("Magnitude", 0)),
                "focal": "",
                "area": g.get("Wilayah", g.get("Dirasakan", "")),
            })
        except (ValueError, TypeError):
            continue

    return quakes


# ============================================================================
# Main Scraper
# ============================================================================

def scrape_bmkg_earthquakes() -> list[dict]:
    """
    Scrape BMKG earthquake data.
    Tries the Nuxt payload first (200 events), falls back to open data API (15 events).
    """
    client = httpx.Client(timeout=15, follow_redirects=True)

    # --- Attempt 1: Nuxt payload (comprehensive, ~200 events) ---
    try:
        print("📡 Fetching BMKG Nuxt payload...")
        resp = client.get(PAYLOAD_URL)
        if resp.status_code == 200:
            raw = resp.json()
            quakes = _parse_nuxt_payload(raw)
            if quakes:
                print(f"✅ Parsed {len(quakes)} earthquakes from Nuxt payload.")
                return quakes
            else:
                print("⚠️  Nuxt payload returned 0 parsed quakes. Trying fallback...")
    except Exception as e:
        print(f"⚠️  Nuxt payload fetch failed: {e}. Trying fallback...")

    # --- Attempt 2: Official open data (15 most recent M5.0+) ---
    try:
        print("📡 Fetching BMKG open data (gempaterkini)...")
        resp = client.get(FALLBACK_URL)
        if resp.status_code == 200:
            quakes = _parse_bmkg_open_data(resp.json())
            print(f"✅ Parsed {len(quakes)} earthquakes from open data.")

            # Also try felt earthquakes
            try:
                resp2 = client.get(FALLBACK_FELT_URL)
                if resp2.status_code == 200:
                    felt = _parse_bmkg_open_data(resp2.json())
                    print(f"✅ Plus {len(felt)} felt earthquakes.")
                    # Merge, avoiding duplicates by eventid
                    seen = {q["eventid"] for q in quakes}
                    for fq in felt:
                        if fq["eventid"] not in seen:
                            quakes.append(fq)
                            seen.add(fq["eventid"])
            except Exception:
                pass

            return quakes
    except Exception as e:
        print(f"❌ All BMKG data sources failed: {e}")

    return []


def save_to_file(quakes: list[dict], path: str = OUTPUT_FILE):
    """Save earthquake data to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    output = {
        "source": "BMKG",
        "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
        "count": len(quakes),
        "earthquakes": quakes,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"💾 Saved {len(quakes)} earthquakes to {path}")


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    quakes = scrape_bmkg_earthquakes()
    if quakes:
        save_to_file(quakes)
    else:
        print("❌ No earthquake data retrieved.")
        sys.exit(1)
