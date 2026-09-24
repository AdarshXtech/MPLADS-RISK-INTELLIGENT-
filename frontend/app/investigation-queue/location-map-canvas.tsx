"use client";

import { useEffect, useRef, useState } from "react";
import type L from "leaflet";
import { Focus, Globe2, RotateCw } from "lucide-react";
import { coordinates, sourceKey, type MapRecord } from "./location-types";

const INDIA_BOUNDS: L.LatLngBoundsExpression = [[6, 67], [37.5, 98.5]];

export default function LocationMapCanvas({ records, selectedKey, onSelect }: { records: MapRecord[]; selectedKey: string | null; onSelect: (source: MapRecord) => void }) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const outlineRef = useRef<L.GeoJSON | null>(null);
  const markers = useRef<Array<{ marker: L.Marker; key: string }>>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [attempt, setAttempt] = useState(0);
  const [streets, setStreets] = useState(false);
  const [tileError, setTileError] = useState(false);
  const [engine, setEngine] = useState<typeof L | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const controller = new AbortController();
    let map: L.Map | undefined;
    let observer: ResizeObserver | undefined;
    async function initialise() {
      try {
        const L = (await import("leaflet")).default;
        if (controller.signal.aborted || !container.current) return;
        setEngine(L);
        map = L.map(container.current, { scrollWheelZoom: false, minZoom: 3, maxZoom: 19, zoomSnap: 0.25, zoomAnimation: false, fadeAnimation: false, markerZoomAnimation: false, attributionControl: true });
        mapRef.current = map;
        map.fitBounds(INDIA_BOUNDS, { padding: [12, 12], animate: false });
        map.attributionControl.setPrefix(false);
        map.attributionControl.addAttribution('India outline: <a href="https://www.geoboundaries.org/countryDownloads.html" target="_blank" rel="noopener noreferrer">geoBoundaries</a> (CC0)');
        L.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);
        observer = new ResizeObserver(() => map?.invalidateSize({ pan: false }));
        observer.observe(container.current);
        const response = await fetch("/maps/india.geojson", { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]) });
        if (!response.ok) throw new Error("Map outline unavailable");
        const geometry = await response.json();
        if (controller.signal.aborted) return;
        outlineRef.current = L.geoJSON(geometry, { interactive: false, style: { color: "#397e8c", weight: 1.5, fillColor: "#deedf0", fillOpacity: 0.8 } }).addTo(map);
        setStatus("ready");
      } catch {
        if (!controller.signal.aborted) setStatus("error");
      }
    }
    void initialise();
    return () => { controller.abort(); observer?.disconnect(); markers.current = []; outlineRef.current = null; mapRef.current = null; map?.remove(); };
  }, [attempt]);

  useEffect(() => {
    const map = mapRef.current;
    const L = engine;
    if (!map || !L || status === "loading") return;
    const layer = L.featureGroup().addTo(map);
    const positions: L.LatLngTuple[] = [];
    markers.current = [];
    records.forEach((source, index) => {
      const point = coordinates(source);
      if (!point) return;
      const letter = index === 0 ? "A" : "B";
      positions.push(point);
      // Opposite anchors keep co-located records selectable without moving their coordinates.
      const marker = L.marker(point, {
        keyboard: true, title: `Point ${letter}: ${source.work_id}`,
        icon: L.divIcon({ className: `comparison-marker marker-${letter.toLowerCase()}`, html: `<span>${letter}</span>`, iconSize: [44, 44], iconAnchor: index === 0 ? [44, 22] : [0, 22] }),
      }).addTo(layer).on("click", () => onSelect(source));
      const element = marker.getElement();
      element?.setAttribute("aria-label", `Point ${letter}: ${source.work_id}`);
      element?.setAttribute("role", "button");
      element?.setAttribute("aria-controls", "comparison-source-detail");
      element?.addEventListener("keydown", (event) => { if (event.key === " " || event.key === "Enter") { event.preventDefault(); event.stopPropagation(); onSelect(source); } });
      markers.current.push({ marker, key: sourceKey(source) });
    });
    if (positions.length === 2) L.polyline(positions, { color: "#526d7b", weight: 2, dashArray: "5 6", interactive: false }).addTo(layer);
    return () => { layer.remove(); markers.current = []; };
  }, [records, status, onSelect, engine]);

  useEffect(() => {
    markers.current.forEach(({ marker, key }) => {
      marker.getElement()?.classList.toggle("is-selected", selectedKey === key);
      marker.getElement()?.setAttribute("aria-pressed", String(selectedKey === key));
      marker.setZIndexOffset(selectedKey === key ? 1000 : 0);
    });
  }, [selectedKey, records, status]);

  useEffect(() => {
    const map = mapRef.current;
    const L = engine;
    if (!map || !L || status === "loading") return;
    outlineRef.current?.setStyle({ fillOpacity: streets ? 0.04 : 0.8 });
    if (!streets) return;
    const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>',
    }).addTo(map);
    const reportTileError = () => setTileError(true);
    tiles.on("tileerror", reportTileError);
    return () => { tiles.off("tileerror", reportTileError); tiles.remove(); };
  }, [streets, status, attempt, engine]);

  function fitPoints() {
    const points = records.flatMap((source) => { const point = coordinates(source); return point ? [point] : []; });
    if (points.length && engine) mapRef.current?.fitBounds(engine.latLngBounds(points), { padding: [64, 64], maxZoom: 17, animate: false });
  }

  const validPoints = records.flatMap((source) => { const point = coordinates(source); return point ? [point] : []; });
  const separation = validPoints.length === 2 && engine ? engine.latLng(validPoints[0]).distanceTo(validPoints[1]) : null;
  const coincident = validPoints.length === 2 && validPoints[0][0] === validPoints[1][0] && validPoints[0][1] === validPoints[1][1];
  return <div className="location-map-tool">
    <div className="map-toolbar">
      <div className="map-view-actions"><button className="secondary-button" type="button" onClick={() => mapRef.current?.fitBounds(INDIA_BOUNDS, { padding: [12, 12], animate: false })} disabled={status === "loading"}><Globe2 size={16} aria-hidden="true" />India view</button><button className="secondary-button" type="button" onClick={fitPoints} disabled={status === "loading" || validPoints.length === 0}><Focus size={16} aria-hidden="true" />Fit locations</button></div>
      <label className="map-layer-toggle"><input type="checkbox" checked={streets} onChange={(event) => { setTileError(false); setStreets(event.target.checked); }} />Street map</label>
    </div>
    <div className="map-canvas-frame"><div className="comparison-map" ref={container} role="region" aria-label="India work location comparison map" aria-busy={status === "loading"} />
    {status === "loading" && <p className="map-loading-overlay">Loading India map...</p>}</div>
    {status === "error" && <div className="map-load-error" role="alert"><p>India outline could not be loaded. Available source markers are retained.</p><button className="secondary-button" type="button" onClick={() => { setStatus("loading"); setAttempt((value) => value + 1); }}><RotateCw size={16} aria-hidden="true" />Retry map</button></div>}
    {streets && tileError && <p className="map-note" role="alert">Street tiles are unavailable. The India outline and source markers remain available.</p>}
    <div className="map-caption"><span>India reference outline; not a cadastral or legal boundary.</span><span>{separation === null ? "Pair distance unavailable" : `Straight-line separation: ${separation < 1000 ? `${separation.toFixed(1)} m` : `${(separation / 1000).toFixed(2)} km`}`}</span></div>
    {coincident && <p className="map-note">Both records have the same verified coordinates. A and B share one location.</p>}
  </div>;
}
