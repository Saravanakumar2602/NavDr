/**
 * useLiveMarker — Lightweight pose pass-through for navigation marker.
 *
 * Design goals:
 * - During active navigation (isNavigating=true + pose updating at 10 Hz), pass
 *   coordinates through directly without interpolation. At 10 Hz / 0.5 m steps the
 *   motion is already smooth — interpolation only adds lag.
 * - When stationary or idle (real GPS at 1 Hz), use simple linear interpolation to
 *   avoid the marker snapping on each fix.
 * - Never clamping animation duration to 350 ms minimum (the old useSmoothMarker
 *   bug that caused the lag at 10 Hz).
 *
 * Replaces useSmoothMarker.
 */
import { useState, useEffect, useRef } from 'react';
import { VehiclePose } from '../types/navigation';
import { calculateHaversineDistance } from '../utils/geo';

interface LiveMarkerState {
  lat: number;
  lon: number;
  heading: number;
}

export function useLiveMarker(
  pose: VehiclePose,
  isNavigating: boolean = false
): LiveMarkerState {
  const [marker, setMarker] = useState<LiveMarkerState>({
    lat: pose.latitude,
    lon: pose.longitude,
    heading: pose.heading ?? 0,
  });

  const prevLatRef = useRef(pose.latitude);
  const prevLonRef = useRef(pose.longitude);
  const prevHeadingRef = useRef(pose.heading ?? 0);
  const lastUpdateRef = useRef(0);
  const animFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const targetLat = pose.latitude;
    const targetLon = pose.longitude;
    const targetHeading = pose.heading ?? prevHeadingRef.current;

    // Guard: reject zero / invalid positions
    if (!targetLat || !targetLon || !Number.isFinite(targetLat) || !Number.isFinite(targetLon)) {
      return;
    }

    // Initial seeding
    if (prevLatRef.current === 0 && prevLonRef.current === 0) {
      prevLatRef.current = targetLat;
      prevLonRef.current = targetLon;
      prevHeadingRef.current = targetHeading;
      setMarker({ lat: targetLat, lon: targetLon, heading: targetHeading });
      lastUpdateRef.current = performance.now();
      return;
    }

    const dist = calculateHaversineDistance(
      prevLatRef.current, prevLonRef.current,
      targetLat, targetLon
    );

    // Large jump guard (>50m teleport) — snap immediately
    if (dist > 50.0) {
      if (animFrameRef.current !== null) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      prevLatRef.current = targetLat;
      prevLonRef.current = targetLon;
      prevHeadingRef.current = targetHeading;
      setMarker({ lat: targetLat, lon: targetLon, heading: targetHeading });
      lastUpdateRef.current = performance.now();
      return;
    }

    // Sub-pixel movement — skip to avoid jitter
    if (dist < 0.05 && Math.abs(targetHeading - prevHeadingRef.current) < 0.5) {
      return;
    }

    // ── ACTIVE NAVIGATION (10 Hz demo) ──────────────────────────────────
    // Pass through directly. No animation window.
    // 0.5 m steps at 10 Hz = smooth continuous motion on screen.
    if (isNavigating) {
      if (animFrameRef.current !== null) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      prevLatRef.current = targetLat;
      prevLonRef.current = targetLon;
      prevHeadingRef.current = targetHeading;
      setMarker({ lat: targetLat, lon: targetLon, heading: targetHeading });

      // Log [UI_POSE] diagnostic once per second
      const now = performance.now();
      if (now - lastUpdateRef.current >= 1000) {
        lastUpdateRef.current = now;
        console.log(
          `[UI_POSE] timestamp=${Date.now()} lat=${targetLat.toFixed(6)} ` +
          `lon=${targetLon.toFixed(6)} heading=${targetHeading.toFixed(1)}`
        );
      }
      return;
    }

    // ── IDLE / REAL GPS (1 Hz) ──────────────────────────────────────────
    // Use interpolation so the marker slides smoothly between fixes.
    const now = performance.now();
    const dt = lastUpdateRef.current > 0
      ? Math.min(1200, Math.max(100, now - lastUpdateRef.current))
      : 800;
    lastUpdateRef.current = now;

    const startLat = prevLatRef.current;
    const startLon = prevLonRef.current;
    const startHeading = prevHeadingRef.current;
    const startTime = now;

    // Shortest-path heading delta
    const dh = ((targetHeading - startHeading + 540) % 360) - 180;

    if (animFrameRef.current !== null) {
      cancelAnimationFrame(animFrameRef.current);
    }

    const animate = () => {
      const elapsed = performance.now() - startTime;
      const t = Math.min(1.0, elapsed / dt);

      const lat = startLat + t * (targetLat - startLat);
      const lon = startLon + t * (targetLon - startLon);
      const heading = ((startHeading + t * dh) % 360 + 360) % 360;

      prevLatRef.current = lat;
      prevLonRef.current = lon;
      prevHeadingRef.current = heading;

      setMarker({ lat, lon, heading: Math.round(heading) });

      if (t < 1.0) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        animFrameRef.current = null;
        prevLatRef.current = targetLat;
        prevLonRef.current = targetLon;
        prevHeadingRef.current = targetHeading;
      }
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current !== null) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
    };
  }, [pose.latitude, pose.longitude, pose.heading, isNavigating]);

  return marker;
}
