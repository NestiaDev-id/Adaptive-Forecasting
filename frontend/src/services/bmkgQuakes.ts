import { BASE_URL } from "@/lib/baseUrl";

export interface BMKGQuake {
  eventid: string;
  datetime: string;
  latitude: number | null;
  longitude: number | null;
  depth_km: number | null;
  magnitude: number | null;
  area: string;
}

export interface BMKGQuakeResponse {
  source: string;
  count: number;
  earthquakes: BMKGQuake[];
}

/**
 * Magnitude-based styling for earthquake markers.
 */
export function quakeMarkerColor(mag: number | null): string {
  if (mag === null) return "#6b7280";
  if (mag >= 5.0) return "#dc2626"; // red — significant
  if (mag >= 4.0) return "#f97316"; // orange — moderate
  if (mag >= 3.0) return "#eab308"; // yellow — light
  return "#a3a3a3";                 // gray — minor
}

export function quakeLabel(mag: number | null): string {
  if (mag === null) return "?";
  if (mag >= 5.0) return "Kuat";
  if (mag >= 4.0) return "Sedang";
  if (mag >= 3.0) return "Ringan";
  return "Mikro";
}

/**
 * Fetch BMKG earthquake data from our backend API.
 */
export async function fetchBMKGQuakes(): Promise<BMKGQuake[]> {
  try {
    const apiKey = import.meta.env.VITE_INTERNAL_API_KEY || "";
    const res = await fetch(`${BASE_URL}/api/public/earthquakes`, {
      headers: {
        ...(apiKey ? { "X-API-Key": apiKey } : {}),
      },
    });
    if (!res.ok) return [];
    const json: BMKGQuakeResponse = await res.json();
    return json.earthquakes || [];
  } catch (e) {
    console.error("BMKG Quake fetch error:", e);
    return [];
  }
}

/**
 * Filter earthquakes within a radius (km) from center.
 * Uses Haversine formula for accurate distance.
 */
export function filterQuakesByRadius(
  quakes: BMKGQuake[],
  centerLat: number,
  centerLon: number,
  radiusKm: number = 1500
): BMKGQuake[] {
  return quakes.filter((q) => {
    if (q.latitude === null || q.longitude === null) return false;
    const dist = haversineKm(centerLat, centerLon, q.latitude, q.longitude);
    return dist <= radiusKm;
  });
}

function haversineKm(
  lat1: number, lon1: number,
  lat2: number, lon2: number
): number {
  const R = 6371; // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
