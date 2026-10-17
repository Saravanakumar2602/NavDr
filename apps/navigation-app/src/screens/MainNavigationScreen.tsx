import React, { useState, useRef } from 'react';
import { View, StyleSheet, Keyboard } from 'react-native';
import { useNavigation } from '../state/NavigationContext';
import { useAppTheme } from '../theme/ThemeContext';
import { TopBar } from '../components/TopBar';
import { OutageBanner } from '../components/OutageBanner';
import { MapViewPlaceholder } from '../components/MapViewPlaceholder';
import { TelemetryPanel } from '../components/TelemetryPanel';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResultsList } from '../components/search/SearchResultsList';
import { DestinationPreviewCard } from '../components/search/DestinationPreviewCard';
import { NavigationHudCard } from '../components/navigation/NavigationHudCard';
import { placeSearchService } from '../services/PlaceSearchService';
import { PlaceSearchResult, Destination } from '../types/navigation';

export const MainNavigationScreen: React.FC = () => {
  const {
    state,
    setDestination,
    clearDestination,
    calculateRoute,
    clearRoute,
    startTurnByTurnNavigation,
    endTurnByTurnNavigation,
    startDemoNavigation,
  } = useNavigation();
  const { theme } = useAppTheme();

  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PlaceSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | undefined>();
  const [isOffline, setIsOffline] = useState<boolean | undefined>();
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced geocoding search handler (400ms debounce)
  const handleQueryChange = (text: string) => {
    setQuery(text);
    setSearchError(undefined);
    setIsOffline(undefined);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (text.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    debounceTimerRef.current = setTimeout(async () => {
      const res = await placeSearchService.search(text);
      setSearchResults(res.results);
      setSearchError(res.error);
      setIsOffline(res.isOffline);
      setIsSearching(false);
    }, 400);
  };

  const handleClearSearch = () => {
    setQuery('');
    setSearchResults([]);
    setIsSearching(false);
    setSearchError(undefined);
    setIsOffline(undefined);
    placeSearchService.cancelSearch();
  };

  const handleSelectResult = (result: PlaceSearchResult) => {
    Keyboard.dismiss();
    const dest: Destination = {
      id: result.id,
      name: result.name,
      address: result.address,
      latitude: result.latitude,
      longitude: result.longitude,
    };
    setDestination(dest);
    handleClearSearch();
  };

  const handleCancelDestination = () => {
    clearDestination();
    clearRoute();
    endTurnByTurnNavigation();
  };

  /**
   * Called when user taps "Start Navigation".
   * This is the ONLY trigger for the demo trajectory lifecycle.
   * The route must already be computed (calculateRoute runs on destination select).
   */
  const handleStartNavigationIntent = async () => {
    console.log('[START_TRACE] UI_CALLBACK');
    console.log('[DEMO_SESSION] START_REQUEST');
    if (state.destination && state.route) {
      await startDemoNavigation();
    } else if (state.destination && !state.route) {
      // Route not yet ready — calculate first then start
      await calculateRoute();
      await startDemoNavigation();
    } else {
      await startDemoNavigation();
    }
  };

  const isNavigatingTurnByTurn =
    state.currentInstruction != null &&
    state.turnByTurnStatus != null &&
    state.turnByTurnStatus !== 'IDLE';

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Compact Header Bar with In-Place Status */}
      <TopBar
        status={state.gnssStatus}
        drState={state.drState}
        outageSeconds={state.outageDurationSeconds}
      />

      {/* GNSS Outage / Status Mode Banner */}
      <OutageBanner
        status={state.gnssStatus}
        outageSeconds={state.outageDurationSeconds}
        confidence={state.confidence}
        speed={state.pose.speed}
        heading={state.pose.heading}
        drState={state.drState}
      />

      {/* Map-Centric Area (75-85% Screen Height) */}
      <View style={styles.mapWrapper}>
        <MapViewPlaceholder
          pose={state.pose}
          gnssPoints={state.gnssTrajectory}
          idrPoints={state.idrTrajectory}
          gnssStatus={state.gnssStatus}
          lastKnownPose={state.lastKnownGnssPose}
          confidence={state.confidence}
          isNavigating={state.isNavigating}
          destination={state.destination}
          route={state.route}
        />

        {/* Turn-by-Turn Navigation HUD Overlay */}
        {isNavigatingTurnByTurn && state.currentInstruction ? (
          <View style={styles.hudOverlay}>
            <NavigationHudCard
              instruction={state.currentInstruction}
              distanceToDestinationMeters={state.distanceToDestinationMeters}
              onEndNavigation={handleCancelDestination}
            />
          </View>
        ) : (
          /* Floating Destination Search Bar when not actively navigating turn-by-turn */
          <View style={styles.searchBarOverlay}>
            <SearchBar
              value={query}
              onChangeText={handleQueryChange}
              onClear={handleClearSearch}
              isLoading={isSearching}
              placeholder="Search destination"
            />

            {/* Real Search Results Dropdown List */}
            <SearchResultsList
              results={searchResults}
              onSelectResult={handleSelectResult}
              isLoading={isSearching}
              error={searchError}
              isOffline={isOffline}
              query={query}
            />
          </View>
        )}

        {/* Selected Destination Preview Bottom Card */}
        {state.destination && !isNavigatingTurnByTurn ? (
          <DestinationPreviewCard
            destination={state.destination}
            route={state.route}
            routeStatus={state.routeStatus}
            routeError={state.routeError}
            onStartNavigation={handleStartNavigationIntent}
            onCancel={handleCancelDestination}
          />
        ) : null}
      </View>

      {/* Compact Navigation Telemetry Bottom Panel */}
      <TelemetryPanel navState={state} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  mapWrapper: {
    flex: 1,
    position: 'relative',
  },
  searchBarOverlay: {
    position: 'absolute',
    top: 12,
    left: 14,
    right: 14,
    zIndex: 30,
  },
  hudOverlay: {
    position: 'absolute',
    top: 12,
    left: 14,
    right: 14,
    zIndex: 30,
  },
});
