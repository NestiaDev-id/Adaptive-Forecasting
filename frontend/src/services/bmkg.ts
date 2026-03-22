const BMKG_BASE = "https://api.bmkg.go.id/publik/prakiraan-cuaca";

export interface BMKGForecast {
  utc_datetime: string;
  local_datetime: string;
  t: number;       // temperature °C
  hu: number;      // humidity %
  weather_desc: string;
  weather_desc_en: string;
  ws: number;      // wind speed km/h
  wd: string;      // wind direction
  tcc: number;     // cloud cover %
  vs_text: string; // visibility
}

export interface BMKGLocation {
  adm4: string;
  provinsi: string;
  kota: string;
  kecamatan: string;
  kelurahan: string;
  lat: number;
  lon: number;
}

export interface BMKGResponse {
  lokasi: BMKGLocation;
  data: BMKGForecast[];
}

// Some well-known BMKG station codes mapped to lat/lon
// Extend this list or use a geocoding lookup for production
const KNOWN_STATIONS: { adm4: string; lat: number; lon: number; label: string }[] = [
  { adm4: "31.71.03.1001", lat: -6.1544, lon: 106.8451, label: "Kemayoran, Jakarta" },
  { adm4: "32.73.01.1001", lat: -6.9175, lon: 107.6191, label: "Bandung" },
  { adm4: "35.78.17.1001", lat: -7.2575, lon: 112.7521, label: "Surabaya" },
  { adm4: "34.04.01.2001", lat: -7.7956, lon: 110.3695, label: "Yogyakarta" },
  { adm4: "51.71.03.1001", lat: -8.6705, lon: 115.2126, label: "Denpasar, Bali" },
  { adm4: "73.71.04.1001", lat: -5.1477, lon: 119.4327, label: "Makassar" },
  { adm4: "61.71.01.1001", lat: -0.0263, lon: 109.3425, label: "Pontianak" },
  { adm4: "21.71.05.1001", lat: 2.9590, lon: 99.0515, label: "Medan" },
  { adm4: "63.71.01.1001", lat: -3.3194, lon: 114.5910, label: "Banjarmasin" },
  { adm4: "71.71.04.1001", lat: 1.4748, lon: 124.8421, label: "Manado" },
];

/**
 * Find the nearest BMKG station to a given lat/lon.
 */
export function findNearestStation(lat: number, lon: number) {
  let nearest = KNOWN_STATIONS[0];
  let minDist = Infinity;

  for (const station of KNOWN_STATIONS) {
    const dlat = station.lat - lat;
    const dlon = station.lon - lon;
    const dist = Math.sqrt(dlat * dlat + dlon * dlon);
    if (dist < minDist) {
      minDist = dist;
      nearest = station;
    }
  }

  return nearest;
}

/**
 * Fetch BMKG weather forecast for a specific adm4 code.
 * BMKG API response structure:
 *   { lokasi: {...}, data: [{ lokasi: {...}, cuaca: [[ {...}, {...} ], [...]] }] }
 * cuaca is a nested array: each inner array is a group of hourly forecasts.
 */
export async function fetchBMKGWeather(adm4: string): Promise<BMKGResponse | null> {
  try {
    const res = await fetch(`${BMKG_BASE}?adm4=${adm4}`);
    if (!res.ok) return null;
    const json = await res.json();

    if (!json?.data || !Array.isArray(json.data) || json.data.length === 0) {
      return null;
    }

    const entry = json.data[0]; // first station entry
    const lokasi = entry.lokasi || json.lokasi || {};

    // Flatten the nested cuaca arrays into a single list
    const forecasts: BMKGForecast[] = [];
    if (entry.cuaca && Array.isArray(entry.cuaca)) {
      for (const group of entry.cuaca) {
        const items = Array.isArray(group) ? group : [group];
        for (const item of items) {
          forecasts.push({
            utc_datetime: item.utc_datetime || "",
            local_datetime: item.local_datetime || "",
            t: Number(item.t) || 0,
            hu: Number(item.hu) || 0,
            weather_desc: String(item.weather_desc || ""),
            weather_desc_en: String(item.weather_desc_en || ""),
            ws: Number(item.ws) || 0,
            wd: String(item.wd || ""),
            tcc: Number(item.tcc) || 0,
            vs_text: String(item.vs_text || ""),
          });
        }
      }
    }

    return {
      lokasi: {
        adm4: lokasi.adm4 || adm4,
        provinsi: lokasi.provinsi || "",
        kota: lokasi.kotkab || "",
        kecamatan: lokasi.kecamatan || "",
        kelurahan: lokasi.desa || "",
        lat: Number(lokasi.lat) || 0,
        lon: Number(lokasi.lon) || 0,
      },
      data: forecasts,
    };
  } catch (e) {
    console.error("BMKG fetch error:", e);
    return null;
  }
}

/**
 * Fetch weather for the nearest station to a lat/lon.
 */
export async function fetchNearestWeather(lat: number, lon: number) {
  const station = findNearestStation(lat, lon);
  const weather = await fetchBMKGWeather(station.adm4);
  return { station, weather };
}
