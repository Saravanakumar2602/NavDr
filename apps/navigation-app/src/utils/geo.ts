/**
 * Calculate Haversine distance in meters between two lat/lng coordinates
 */
export function calculateHaversineDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000; // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Calculate median of a numeric array
 */
export function calculateMedian(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const half = Math.floor(sorted.length / 2);
  if (sorted.length % 2 !== 0) {
    return sorted[half];
  }
  return (sorted[half - 1] + sorted[half]) / 2.0;
}

const EARTH_RADIUS_METERS = 6371000;

/**
 * Convert Geodetic (Lat, Lon) to Local ENU (East, North) meters relative to reference origin
 */
export function latLngToEnu(
  lat: number,
  lon: number,
  refLat: number,
  refLon: number
): { e: number; n: number } {
  const dLatRad = ((lat - refLat) * Math.PI) / 180;
  const dLonRad = ((lon - refLon) * Math.PI) / 180;
  const refLatRad = (refLat * Math.PI) / 180;

  const e = dLonRad * EARTH_RADIUS_METERS * Math.cos(refLatRad);
  const n = dLatRad * EARTH_RADIUS_METERS;
  return { e, n };
}

/**
 * Convert Local ENU (East, North) meters back to Geodetic (Lat, Lon) relative to reference origin
 */
export function enuToLatLng(
  e: number,
  n: number,
  refLat: number,
  refLon: number
): { lat: number; lon: number } {
  const refLatRad = (refLat * Math.PI) / 180;
  const dLatRad = n / EARTH_RADIUS_METERS;
  const dLonRad = e / (EARTH_RADIUS_METERS * Math.cos(refLatRad));

  const lat = refLat + (dLatRad * 180) / Math.PI;
  const lon = refLon + (dLonRad * 180) / Math.PI;
  return { lat, lon };
}

/**
 * Circular angle filter handling 359° -> 1° wrap-around safely using vector components
 */
export function filterCircularAngle(
  prevDeg: number | null,
  newDeg: number,
  alpha: number = 0.35
): number {
  if (prevDeg === null || isNaN(prevDeg)) {
    return Math.round(((newDeg % 360) + 360) % 360);
  }

  const pRad = (prevDeg * Math.PI) / 180;
  const nRad = (newDeg * Math.PI) / 180;

  const x = (1 - alpha) * Math.cos(pRad) + alpha * Math.cos(nRad);
  const y = (1 - alpha) * Math.sin(pRad) + alpha * Math.sin(nRad);

  const avgRad = Math.atan2(y, x);
  const avgDeg = (avgRad * 180) / Math.PI;

  return Math.round(((avgDeg % 360) + 360) % 360);
}
