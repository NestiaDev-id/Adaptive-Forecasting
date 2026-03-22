import { useState, useEffect } from "react";

interface GeolocationState {
  lat: number | null;
  lon: number | null;
  accuracy: number | null;
  loading: boolean;
  error: string | null;
}

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    lat: null,
    lon: null,
    accuracy: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    if (!navigator.geolocation) {
      setState((s) => ({
        ...s,
        loading: false,
        error: "Geolocation tidak didukung oleh browser ini.",
      }));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setState({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          loading: false,
          error: null,
        });
      },
      (err) => {
        // Fallback: Jakarta center
        setState({
          lat: -6.2088,
          lon: 106.8456,
          accuracy: null,
          loading: false,
          error: `GPS gagal: ${err.message}. Menggunakan lokasi default (Jakarta).`,
        });
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
  }, []);

  return state;
}
