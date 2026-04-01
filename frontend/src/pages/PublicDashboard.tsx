import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import {
  MapPin, Thermometer, Droplets, Wind, Eye,
  CloudRain, AlertTriangle, RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { useGeolocation } from "@/hooks/useGeolocation";
import { fetchNearestWeather, type BMKGForecast } from "@/services/bmkg";
import {
  fetchEONETEvents,
  filterByRadius,
  categorizeEvent,
  EVENT_STYLES,
  type EONETEvent,
} from "@/services/nasa";
import {
  fetchBMKGQuakes,
  filterQuakesByRadius,
  quakeMarkerColor,
  quakeLabel,
  type BMKGQuake,
} from "@/services/bmkgQuakes";

// Fix Leaflet default marker icons in bundlers
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

/** Animate map to user location on initial load. */
function FlyToLocation({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  const flown = useRef(false);
  useEffect(() => {
    if (!flown.current) {
      map.flyTo([lat, lon], 8, { duration: 1.5 });
      flown.current = true;
    }
  }, [lat, lon, map]);
  return null;
}

interface FlyTarget {
  lat: number;
  lon: number;
  zoom: number;
  eventId: string;
}

/** Controller that flies map to a target when flyToTarget changes. */
function MapController({ target }: { target: FlyTarget | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) {
      map.flyTo([target.lat, target.lon], target.zoom, { duration: 1.2 });
    }
  }, [target, map]);
  return null;
}

/** Create colored circle icons for event markers. */
function createEventIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:14px;height:14px;border-radius:50%;
      background:${color};border:2px solid white;
      box-shadow:0 0 6px ${color}88;
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export default function PublicDashboard() {
  const geo = useGeolocation();
  const [weather, setWeather] = useState<BMKGForecast[] | null>(null);
  const [stationLabel, setStationLabel] = useState("");
  const [events, setEvents] = useState<EONETEvent[]>([]);
  const [quakes, setQuakes] = useState<BMKGQuake[]>([]);
  const [loadingWeather, setLoadingWeather] = useState(true);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [loadingQuakes, setLoadingQuakes] = useState(true);
  const [flyToTarget, setFlyToTarget] = useState<FlyTarget | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const markerRefs = useRef<Record<string, L.Marker>>({});

  // Fetch weather when GPS ready
  useEffect(() => {
    if (geo.lat && geo.lon) {
      setLoadingWeather(true);
      fetchNearestWeather(geo.lat, geo.lon)
        .then(({ station, weather: w }) => {
          setStationLabel(station.label);
          setWeather(w?.data || null);
        })
        .finally(() => setLoadingWeather(false));
    }
  }, [geo.lat, geo.lon]);

  // Fetch NASA events
  useEffect(() => {
    setLoadingEvents(true);
    fetchEONETEvents(80)
      .then((all) => {
        if (geo.lat && geo.lon) {
          setEvents(filterByRadius(all, geo.lat, geo.lon, 30));
        } else {
          setEvents(all.slice(0, 30));
        }
      })
      .finally(() => setLoadingEvents(false));
  }, [geo.lat, geo.lon]);

  // Fetch BMKG earthquakes
  useEffect(() => {
    setLoadingQuakes(true);
    fetchBMKGQuakes()
      .then((all) => {
        if (geo.lat && geo.lon) {
          setQuakes(filterQuakesByRadius(all, geo.lat, geo.lon, 1500));
        } else {
          // Default: show all Indonesian quakes
          setQuakes(all.slice(0, 100));
        }
      })
      .finally(() => setLoadingQuakes(false));
  }, [geo.lat, geo.lon]);

  const currentWeather = weather?.[0];
  const mapCenter: [number, number] = [geo.lat ?? -2.5, geo.lon ?? 118];
  const mapZoom = geo.lat ? 6 : 4;

  return (
    <div className="h-[calc(100vh-0px)] flex flex-col">
      {/* Hero header */}
      <motion.div
        className="px-6 py-4 border-b border-border/50 bg-card/30 backdrop-blur-md"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
              <MapPin className="h-5 w-5 text-blue-400" />
              Global Weather Monitor
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Real-time cuaca & event bencana · BMKG + NASA EONET
            </p>
          </div>
          <div className="flex items-center gap-2">
            {geo.loading ? (
              <Badge variant="outline" className="text-xs gap-1">
                <Spinner className="h-3 w-3" /> Mencari lokasi...
              </Badge>
            ) : (
              <Badge variant="outline" className="text-xs gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                {stationLabel || "Indonesia"}
              </Badge>
            )}
            <Badge variant="secondary" className="text-xs gap-1">
              <AlertTriangle className="h-3 w-3" />
              {events.length} Events
            </Badge>
            <Badge variant="secondary" className="text-xs gap-1 bg-red-500/10 text-red-400 border-red-500/30">
              🔴 {quakes.length} Gempa
            </Badge>
          </div>
        </div>
      </motion.div>

      {/* Content: Map + Side panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          <MapContainer
            center={mapCenter}
            zoom={mapZoom}
            className="h-full w-full z-0"
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Fly to user */}
            {geo.lat && geo.lon && <FlyToLocation lat={geo.lat} lon={geo.lon} />}

            {/* Controller for event click → fly */}
            <MapController target={flyToTarget} />

            {/* User location marker + radius */}
            {geo.lat && geo.lon && (
              <>
                <Marker position={[geo.lat, geo.lon]}>
                  <Popup>
                    <strong>📍 Lokasi Anda</strong>
                    <br />
                    {geo.lat.toFixed(4)}, {geo.lon.toFixed(4)}
                    {geo.accuracy && <><br />Akurasi: {Math.round(geo.accuracy)}m</>}
                  </Popup>
                </Marker>
                <Circle
                  center={[geo.lat, geo.lon]}
                  radius={50000}
                  pathOptions={{
                    color: "#3b82f6",
                    fillColor: "#3b82f680",
                    fillOpacity: 0.08,
                    weight: 1,
                  }}
                />
              </>
            )}

            {/* NASA EONET event markers */}
            {events.map((event) => {
              if (!event.geometry.length) return null;
              const lastGeo = event.geometry[event.geometry.length - 1];
              const [lon, lat] = lastGeo.coordinates;
              const category = categorizeEvent(event.categories);
              const style = EVENT_STYLES[category];

              return (
                <Marker
                  key={event.id}
                  position={[lat, lon]}
                  icon={createEventIcon(style.color)}
                  ref={(ref) => { if (ref) markerRefs.current[event.id] = ref; }}
                  eventHandlers={{
                    click: () => setSelectedEventId(event.id),
                  }}
                >
                  <Popup>
                    <div className="text-xs space-y-1">
                      <strong>{style.emoji} {event.title}</strong>
                      <br />
                      <span className="text-gray-500">{style.label}</span>
                      {lastGeo.magnitudeValue && (
                        <><br />Magnitude: {lastGeo.magnitudeValue} {lastGeo.magnitudeUnit}</>
                      )}
                      <br />
                      <span className="text-gray-400">
                        {new Date(lastGeo.date).toLocaleDateString("id-ID")}
                      </span>
                      <br />
                      <span className="text-gray-400 font-mono">
                        📍 {lat.toFixed(4)}, {lon.toFixed(4)}
                      </span>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

            {/* BMKG Earthquake markers */}
            {quakes.map((quake) => {
              if (quake.latitude === null || quake.longitude === null) return null;
              const color = quakeMarkerColor(quake.magnitude);
              return (
                <Marker
                  key={quake.eventid}
                  position={[quake.latitude, quake.longitude]}
                  icon={createEventIcon(color)}
                  ref={(ref) => { if (ref) markerRefs.current[quake.eventid] = ref; }}
                  eventHandlers={{
                    click: () => setSelectedEventId(quake.eventid),
                  }}
                >
                  <Popup>
                    <div className="text-xs space-y-1">
                      <strong>🔴 Gempa M{quake.magnitude?.toFixed(1)}</strong>
                      <br />
                      <span className="text-gray-500">{quake.area}</span>
                      <br />
                      <span className="text-gray-400">
                        Kedalaman: {quake.depth_km} km
                      </span>
                      <br />
                      <span className="text-gray-400 text-[10px]">
                        {quake.datetime}
                      </span>
                      <br />
                      <span className="text-gray-400 font-mono text-[10px]">
                        📍 {quake.latitude.toFixed(4)}, {quake.longitude.toFixed(4)}
                      </span>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>

          {/* Event legend overlay */}
          <motion.div
            className="absolute bottom-4 left-4 bg-card/90 backdrop-blur-md rounded-lg p-3 border border-border/50 shadow-lg z-[1000]"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <p className="text-[10px] font-semibold text-muted-foreground mb-1.5">LEGENDA EVENT</p>
            <div className="space-y-1">
              {Object.entries(EVENT_STYLES).map(([, style]) => (
                <div key={style.label} className="flex items-center gap-1.5 text-[10px] text-foreground">
                  <span
                    className="h-2.5 w-2.5 rounded-full inline-block"
                    style={{ background: style.color }}
                  />
                  {style.emoji} {style.label}
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Side panel */}
        <motion.div
          className="w-80 border-l border-border/50 bg-card/30 backdrop-blur-md overflow-y-auto"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          <div className="p-4 space-y-4">
            {/* Current Weather Card */}
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                    <CloudRain className="h-3.5 w-3.5 text-blue-400" />
                    Cuaca Saat Ini
                  </h3>
                  {loadingWeather && <Spinner className="h-3 w-3" />}
                </div>

                <AnimatePresence mode="wait">
                  {currentWeather ? (
                    <motion.div
                      key="weather"
                      className="space-y-2"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="text-center py-2">
                        <p className="text-3xl font-bold text-foreground">
                          {currentWeather.t}°C
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {currentWeather.weather_desc}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {stationLabel}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Droplets className="h-3 w-3 text-blue-400" />
                          {currentWeather.hu}%
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Wind className="h-3 w-3 text-teal-400" />
                          {currentWeather.ws} km/h {currentWeather.wd}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Thermometer className="h-3 w-3 text-orange-400" />
                          Tutupan: {currentWeather.tcc}%
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Eye className="h-3 w-3 text-purple-400" />
                          {currentWeather.vs_text}
                        </div>
                      </div>
                    </motion.div>
                  ) : !loadingWeather ? (
                    <motion.p
                      key="no-weather"
                      className="text-xs text-muted-foreground text-center py-4"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      Data cuaca tidak tersedia untuk lokasi ini.
                    </motion.p>
                  ) : null}
                </AnimatePresence>
              </CardContent>
            </Card>

            {/* Forecast 3 Days */}
            {weather && weather.length > 1 && (
              <Card className="bg-card/50 border-border/50">
                <CardContent className="p-4">
                  <h3 className="text-xs font-semibold text-muted-foreground mb-3 flex items-center gap-1.5">
                    <RefreshCw className="h-3.5 w-3.5 text-purple-400" />
                    Prakiraan (3 Hari)
                  </h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {weather.slice(0, 12).map((fc, i) => (
                      <motion.div
                        key={i}
                        className="flex items-center justify-between py-1.5 px-2 rounded text-xs hover:bg-secondary/30 transition-colors"
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + i * 0.05 }}
                      >
                        <span className="text-muted-foreground font-mono text-[10px] w-28">
                          {fc.local_datetime?.split(" ")[0]?.slice(5)} {fc.local_datetime?.split(" ")[1]?.slice(0, 5)}
                        </span>
                        <span className="font-semibold text-foreground">
                          {fc.t}°C
                        </span>
                        <span className="text-muted-foreground truncate max-w-20 text-right">
                          {fc.weather_desc}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* BMKG Earthquakes List */}
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                    🔴 Gempa Bumi BMKG
                  </h3>
                  {loadingQuakes && <Spinner className="h-3 w-3" />}
                </div>
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {quakes.length > 0 ? quakes.slice(0, 30).map((quake, i) => (
                    <motion.div
                      key={quake.eventid}
                      className={`flex items-start gap-2 py-1.5 px-2 rounded text-xs transition-colors cursor-pointer ${
                        selectedEventId === quake.eventid
                          ? "bg-red-500/10 ring-1 ring-red-500/30"
                          : "hover:bg-secondary/30"
                      }`}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + i * 0.03 }}
                      onClick={() => {
                        if (quake.latitude === null || quake.longitude === null) return;
                        setSelectedEventId(quake.eventid);
                        setFlyToTarget({ lat: quake.latitude, lon: quake.longitude, zoom: 10, eventId: quake.eventid });
                        setTimeout(() => {
                          markerRefs.current[quake.eventid]?.openPopup();
                        }, 1300);
                      }}
                      whileHover={{ x: 2 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <span
                        className="h-2 w-2 rounded-full mt-1 shrink-0"
                        style={{ background: quakeMarkerColor(quake.magnitude) }}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="text-foreground truncate font-medium">
                          M{quake.magnitude?.toFixed(1)} — {quake.area}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {quakeLabel(quake.magnitude)} · {quake.depth_km} km · {quake.datetime?.split("  ")[0]}
                        </p>
                      </div>
                      <MapPin className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
                    </motion.div>
                  )) : !loadingQuakes ? (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      Tidak ada data gempa.
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>

            {/* NASA EONET Events List */}
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />
                    Event Aktif (NASA)
                  </h3>
                  {loadingEvents && <Spinner className="h-3 w-3" />}
                </div>
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {events.length > 0  ? events.map((event, i) => {
                    const category = categorizeEvent(event.categories);
                    const style = EVENT_STYLES[category];
                    return (
                      <motion.div
                        key={event.id}
                        className={`flex items-start gap-2 py-1.5 px-2 rounded text-xs transition-colors cursor-pointer ${
                          selectedEventId === event.id
                            ? "bg-primary/10 ring-1 ring-primary/30"
                            : "hover:bg-secondary/30"
                        }`}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 + i * 0.04 }}
                        onClick={() => {
                          if (!event.geometry.length) return;
                          const g = event.geometry[event.geometry.length - 1];
                          const [eLon, eLat] = g.coordinates;
                          setSelectedEventId(event.id);
                          setFlyToTarget({ lat: eLat, lon: eLon, zoom: 10, eventId: event.id });
                          setTimeout(() => {
                            markerRefs.current[event.id]?.openPopup();
                          }, 1300);
                        }}
                        whileHover={{ x: 2 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <span
                          className="h-2 w-2 rounded-full mt-1 shrink-0"
                          style={{ background: style.color }}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="text-foreground truncate font-medium">
                            {event.title}
                          </p>
                          <p className="text-[10px] text-muted-foreground">
                            {style.label} ·{" "}
                            {event.geometry[event.geometry.length - 1]?.date
                              ? new Date(event.geometry[event.geometry.length - 1].date).toLocaleDateString("id-ID")
                              : ""}
                          </p>
                        </div>
                        <MapPin className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
                      </motion.div>
                    );
                  }) : !loadingEvents ? (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      Tidak ada event aktif dalam radius.
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
