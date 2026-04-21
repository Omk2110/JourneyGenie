"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import styles from "./MapView.module.css";

// Day colors for markers and routes
const DAY_COLORS = [
  "#6366f1", // destination
  "#3b82f6", // day 1
  "#06b6d4", // day 2
  "#10b981", // day 3
  "#f59e0b", // day 4
  "#ec4899", // day 5
  "#8b5cf6", // day 6
  "#ef4444", // day 7
  "#14b8a6", // day 8
  "#f97316", // day 9
  "#a855f7", // day 10
];

function createCustomIcon(color, label) {
  return L.divIcon({
    className: styles.customMarker,
    html: `<div style="
      background: ${color};
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 12px;
      font-weight: 700;
      box-shadow: 0 2px 8px ${color}88;
      border: 2px solid white;
    ">${label}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
}

export default function MapView({ mapData, itinerary }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // Filter points with valid coordinates
    const validPoints = (mapData || []).filter(
      (p) => p.latitude !== 0 || p.longitude !== 0
    );

    if (validPoints.length === 0) return;

    // Calculate center from all points
    const center = validPoints.reduce(
      (acc, p) => [acc[0] + p.latitude / validPoints.length, acc[1] + p.longitude / validPoints.length],
      [0, 0]
    );

    // Create map
    const map = L.map(mapRef.current, {
      center: center,
      zoom: 13,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    // Dark tile layer
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        maxZoom: 19,
      }
    ).addTo(map);

    // Group points by day
    const dayGroups = {};
    validPoints.forEach((point) => {
      const day = point.day || 0;
      if (!dayGroups[day]) dayGroups[day] = [];
      dayGroups[day].push(point);
    });

    // Add markers and routes for each day
    Object.entries(dayGroups).forEach(([day, points]) => {
      const dayNum = parseInt(day);
      const color = DAY_COLORS[dayNum % DAY_COLORS.length];

      // Sort by order
      points.sort((a, b) => (a.order || 0) - (b.order || 0));

      // Add markers
      points.forEach((point) => {
        const label = dayNum === 0 ? "★" : `${point.order || ""}`;
        const icon = createCustomIcon(color, label);

        const marker = L.marker([point.latitude, point.longitude], { icon });

        const popupContent = `
          <div style="min-width: 150px;">
            <strong style="font-size: 14px;">${point.name}</strong><br/>
            <span style="color: #94a3b8; font-size: 12px;">
              ${dayNum === 0 ? "📍 Destination" : `Day ${dayNum} • Stop ${point.order}`}
            </span><br/>
            <span style="color: #64748b; font-size: 11px;">
              ${point.category || ""}
            </span>
          </div>
        `;

        marker.bindPopup(popupContent);
        marker.addTo(map);
      });

      // Draw route lines between points in the same day
      if (points.length >= 2 && dayNum > 0) {
        const routeCoords = points.map((p) => [p.latitude, p.longitude]);
        L.polyline(routeCoords, {
          color: color,
          weight: 3,
          opacity: 0.7,
          dashArray: "8, 8",
        }).addTo(map);
      }
    });

    // Fit bounds to show all markers
    const bounds = L.latLngBounds(validPoints.map((p) => [p.latitude, p.longitude]));
    map.fitBounds(bounds, { padding: [40, 40] });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [mapData]);

  // Legend
  const days = [...new Set((mapData || []).filter((p) => p.day > 0).map((p) => p.day))].sort();

  return (
    <div className={styles.container}>
      <div ref={mapRef} className={styles.map} id="travel-map" />
      {days.length > 0 && (
        <div className={styles.legend}>
          {days.map((day) => (
            <div key={day} className={styles.legendItem}>
              <span
                className={styles.legendDot}
                style={{ background: DAY_COLORS[day % DAY_COLORS.length] }}
              />
              <span>Day {day}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
