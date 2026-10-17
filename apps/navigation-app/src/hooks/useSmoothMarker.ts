import { useState, useEffect, useRef } from 'react';
import { VehiclePose } from '../types/navigation';
import { calculateHaversineDistance } from '../utils/geo';

interface SmoothMarkerState {
  animatedLat: number;
  animatedLon: number;
  animatedHeading: number;
}

export function useSmoothMarker(
  pose: VehiclePose,
  isStationary: boolean = false
): SmoothMarkerState {
  const [animatedPos, setAnimatedPos] = useState<SmoothMarkerState>({
    animatedLat: pose.latitude,
    animatedLon: pose.longitude,
    animatedHeading: pose.heading || 0,
  });

  const currLatRef = useRef<number>(pose.latitude);
  const currLonRef = useRef<number>(pose.longitude);
  const currHeadingRef = useRef<number>(pose.heading || 0);

  const startLatRef = useRef<number>(pose.latitude);
  const startLonRef = useRef<number>(pose.longitude);
  const startHeadingRef = useRef<number>(pose.heading || 0);

  const targetLatRef = useRef<number>(pose.latitude);
  const targetLonRef = useRef<number>(pose.longitude);
  const targetHeadingRef = useRef<number>(pose.heading || 0);
  const deltaHeadingRef = useRef<number>(0);

  const lastFixTimeRef = useRef<number>(0);
  const animStartTimeRef = useRef<number>(0);
  const animDurationRef = useRef<number>(600);
  const animFrameIdRef = useRef<number | null>(null);

  useEffect(() => {
    const now = performance.now();
    const targetLat = pose.latitude;
    const targetLon = pose.longitude;
    const targetHeading = pose.heading !== null ? pose.heading : currHeadingRef.current;

    const dist = calculateHaversineDistance(
      currLatRef.current,
      currLonRef.current,
      targetLat,
      targetLon
    );

    // 1. Initial Load or Large-Jump / Teleport Guard (>50m jump)
    if (currLatRef.current === 0 || currLonRef.current === 0 || dist > 50.0) {
      if (animFrameIdRef.current !== null) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      currLatRef.current = targetLat;
      currLonRef.current = targetLon;
      currHeadingRef.current = targetHeading;
      setAnimatedPos({
        animatedLat: targetLat,
        animatedLon: targetLon,
        animatedHeading: targetHeading,
      });
      lastFixTimeRef.current = now;
      return;
    }

    // 2. Stationary Guard: Hold position steady when stationary
    if (isStationary || pose.speed === 0 || dist < 0.15) {
      if (animFrameIdRef.current !== null) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      currLatRef.current = targetLat;
      currLonRef.current = targetLon;
      currHeadingRef.current = targetHeading;
      setAnimatedPos({
        animatedLat: targetLat,
        animatedLon: targetLon,
        animatedHeading: targetHeading,
      });
      lastFixTimeRef.current = now;
      return;
    }

    // 3. Setup Interpolation Frame
    let dt = lastFixTimeRef.current > 0 ? now - lastFixTimeRef.current : 600;
    dt = Math.min(1200, Math.max(350, dt));

    lastFixTimeRef.current = now;
    animStartTimeRef.current = now;
    animDurationRef.current = dt;

    startLatRef.current = currLatRef.current;
    startLonRef.current = currLonRef.current;
    startHeadingRef.current = currHeadingRef.current;

    targetLatRef.current = targetLat;
    targetLonRef.current = targetLon;
    targetHeadingRef.current = targetHeading;

    // Shortest-path circular angle delta: handles 359° -> 1° rotating +2° through North
    const dh = ((targetHeading - startHeadingRef.current + 540) % 360) - 180;
    deltaHeadingRef.current = dh;

    // 4. Start 60fps RequestAnimationFrame Loop
    if (animFrameIdRef.current !== null) {
      cancelAnimationFrame(animFrameIdRef.current);
    }

    const animate = () => {
      const elapsed = performance.now() - animStartTimeRef.current;
      const progress = Math.min(1.0, Math.max(0.0, elapsed / animDurationRef.current));

      // Linear spatial interpolation
      const lat = startLatRef.current + progress * (targetLatRef.current - startLatRef.current);
      const lon = startLonRef.current + progress * (targetLonRef.current - startLonRef.current);

      // Shortest-path circular heading interpolation
      const heading =
        ((startHeadingRef.current + progress * deltaHeadingRef.current) % 360 + 360) % 360;

      currLatRef.current = lat;
      currLonRef.current = lon;
      currHeadingRef.current = heading;

      setAnimatedPos({
        animatedLat: lat,
        animatedLon: lon,
        animatedHeading: Math.round(heading),
      });

      if (progress < 1.0) {
        animFrameIdRef.current = requestAnimationFrame(animate);
      } else {
        animFrameIdRef.current = null;
      }
    };

    animFrameIdRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameIdRef.current !== null) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
    };
  }, [pose.latitude, pose.longitude, pose.heading, pose.speed, isStationary]);

  return animatedPos;
}
