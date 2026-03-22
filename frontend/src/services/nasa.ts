const EONET_BASE = "https://eonet.gsfc.nasa.gov/api/v3";

export interface EONETGeometry {
  magnitudeValue: number | null;
  magnitudeUnit: string | null;
  date: string;
  type: string;
  coordinates: [number, number]; // [lon, lat]
}

export interface EONETEvent {
  id: string;
  title: string;
  description: string | null;
  link: string;
  closed: string | null;
  categories: { id: string; title: string }[];
  geometry: EONETGeometry[];
}

export type EventCategory =
  | "earthquakes"
  | "severeStorms"
  | "floods"
  | "wildfires"
  | "volcanoes"
  | "other";

/**
 * Map EONET category IDs to our simplified types.
 */
export function categorizeEvent(categories: { id: string; title: string }[]): EventCategory {
  for (const cat of categories) {
    const id = cat.id.toLowerCase();
    if (id.includes("earthquake") || id === "earthquakes") return "earthquakes";
    if (id.includes("storm") || id.includes("cyclone")) return "severeStorms";
    if (id.includes("flood")) return "floods";
    if (id.includes("fire") || id.includes("wildfire")) return "wildfires";
    if (id.includes("volcan")) return "volcanoes";
  }
  return "other";
}

/**
 * Color and emoji for each event category.
 */
export const EVENT_STYLES: Record<EventCategory, { color: string; emoji: string; label: string }> =
  {
    earthquakes: { color: "#ef4444", emoji: "🔴", label: "Gempa Bumi" },
    severeStorms: { color: "#eab308", emoji: "🟡", label: "Badai" },
    floods: { color: "#3b82f6", emoji: "🔵", label: "Banjir" },
    wildfires: { color: "#f97316", emoji: "🟠", label: "Kebakaran" },
    volcanoes: { color: "#a855f7", emoji: "🟣", label: "Gunung Berapi" },
    other: { color: "#6b7280", emoji: "⚪", label: "Lainnya" },
  };

/**
 * Fetch active EONET events from NASA.
 */
export async function fetchEONETEvents(limit = 50): Promise<EONETEvent[]> {
  try {
    const res = await fetch(`${EONET_BASE}/events?status=open&limit=${limit}`);
    if (!res.ok) return [];
    const json = await res.json();
    return json.events || [];
  } catch (e) {
    console.error("NASA EONET fetch error:", e);
    return [];
  }
}

/**
 * Filter events within a radius (degrees) from a center point.
 */
export function filterByRadius(
  events: EONETEvent[],
  centerLat: number,
  centerLon: number,
  radiusDeg = 15
): EONETEvent[] {
  return events.filter((event) => {
    if (!event.geometry.length) return false;
    const lastGeo = event.geometry[event.geometry.length - 1];
    const [lon, lat] = lastGeo.coordinates;
    const dlat = lat - centerLat;
    const dlon = lon - centerLon;
    return Math.sqrt(dlat * dlat + dlon * dlon) <= radiusDeg;
  });
}
