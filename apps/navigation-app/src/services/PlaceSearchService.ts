import { PlaceSearchResult } from '../types/navigation';

export interface SearchResponse {
  results: PlaceSearchResult[];
  error?: string;
  isOffline?: boolean;
}

const OFFLINE_PRESET_PLACES: PlaceSearchResult[] = [
  {
    id: 'preset_vadasithur',
    name: 'Vadasithur',
    address: 'Vadasithur, Kinathukadavu, Coimbatore, Tamil Nadu, India',
    latitude: 10.8367367,
    longitude: 77.0824874,
    type: 'village',
  },
  {
    id: 'preset_sece',
    name: 'Sri Eshwar College of Engineering',
    address: 'Kondampatti, Vadasithur Road, Kinathukadavu, Coimbatore, Tamil Nadu 641202',
    latitude: 10.8280458,
    longitude: 77.0610151,
    type: 'college',
  },
  {
    id: 'preset_kinathukadavu',
    name: 'Kinathukadavu',
    address: 'Kinathukadavu, Coimbatore, Tamil Nadu',
    latitude: 10.8142,
    longitude: 77.0215,
    type: 'town',
  },
  {
    id: 'preset_pollachi',
    name: 'Pollachi',
    address: 'Pollachi, Coimbatore, Tamil Nadu',
    latitude: 10.6609,
    longitude: 77.0048,
    type: 'town',
  },
];

export class PlaceSearchService {
  private baseUrl: string = 'https://nominatim.openstreetmap.org/search';
  private currentAbortController: AbortController | null = null;

  /**
   * Search for places matching the query string using Nominatim Geocoding API with offline presets fallback.
   */
  public async search(query: string): Promise<SearchResponse> {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || trimmedQuery.length < 2) {
      return { results: [] };
    }

    const qLower = trimmedQuery.toLowerCase();
    const matchingPresets = OFFLINE_PRESET_PLACES.filter(
      (p) => p.name.toLowerCase().includes(qLower) || p.address.toLowerCase().includes(qLower)
    );

    // Abort previous in-flight request if user keeps typing
    if (this.currentAbortController) {
      this.currentAbortController.abort();
    }

    this.currentAbortController = new AbortController();
    const signal = this.currentAbortController.signal;

    const timeoutId = setTimeout(() => {
      this.currentAbortController?.abort();
    }, 8000);

    try {
      const url = `${this.baseUrl}?q=${encodeURIComponent(
        trimmedQuery
      )}&format=json&addressdetails=1&limit=10&accept-language=en`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'User-Agent': 'NavDR-NavigationApp/1.0 (contact: navdr@sih2026.internal)',
          'Accept-Language': 'en',
          Accept: 'application/json',
        },
        signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return {
          results: matchingPresets,
          error: matchingPresets.length > 0 ? undefined : `Geocoding service error (${response.status})`,
        };
      }

      const data = await response.json();

      if (!Array.isArray(data)) {
        return { results: matchingPresets };
      }

      const remoteResults: PlaceSearchResult[] = data
        .map((item: any, index: number) => {
          const rawName = item.name || item.display_name?.split(',')[0] || 'Unknown Place';
          const parts = (item.display_name || '').split(',');
          const address = parts.length > 1 ? parts.slice(1).join(',').trim() : item.display_name || '';

          return {
            id: String(item.place_id || `place_${index}_${Date.now()}`),
            name: rawName,
            address: address || rawName,
            latitude: parseFloat(item.lat),
            longitude: parseFloat(item.lon),
            type: item.type || item.class || 'location',
          };
        })
        .filter((res) => Number.isFinite(res.latitude) && Number.isFinite(res.longitude));

      // Combine remote results and matching presets without duplicate names
      const combined = [...matchingPresets];
      for (const rem of remoteResults) {
        if (!combined.some((c) => c.name.toLowerCase() === rem.name.toLowerCase())) {
          combined.push(rem);
        }
      }

      return { results: combined };
    } catch (err: any) {
      clearTimeout(timeoutId);

      if (err.name === 'AbortError') {
        return { results: matchingPresets };
      }

      const isNetworkError =
        err.message?.includes('Failed to fetch') ||
        err.message?.includes('NetworkError') ||
        err.message?.includes('Network request failed');

      return {
        results: matchingPresets,
        error: matchingPresets.length > 0 ? undefined : isNetworkError ? 'Search unavailable offline' : 'Unable to complete search request',
        isOffline: isNetworkError,
      };
    } finally {
      this.currentAbortController = null;
    }
  }

  public cancelSearch(): void {
    if (this.currentAbortController) {
      this.currentAbortController.abort();
      this.currentAbortController = null;
    }
  }
}

export const placeSearchService = new PlaceSearchService();
