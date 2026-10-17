import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Destination, Route, RouteStatus, RouteError } from '../../types/navigation';
import { useAppTheme } from '../../theme/ThemeContext';

interface DestinationPreviewCardProps {
  destination: Destination;
  route?: Route | null;
  routeStatus?: RouteStatus;
  routeError?: RouteError | null;
  onStartNavigation: () => void;
  onCancel: () => void;
}

export const DestinationPreviewCard: React.FC<DestinationPreviewCardProps> = ({
  destination,
  route,
  routeStatus = 'NONE',
  routeError,
  onStartNavigation,
  onCancel,
}) => {
  const { theme } = useAppTheme();

  const formattedDistance = route?.distanceMeters
    ? route.distanceMeters >= 1000
      ? `${(route.distanceMeters / 1000).toFixed(1)} km`
      : `${Math.round(route.distanceMeters)} m`
    : null;

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.card,
          borderColor: theme.colors.cardBorder,
        },
      ]}
    >
      <View style={styles.headerRow}>
        <View style={styles.iconBox}>
          <Text style={styles.destIcon}>📍</Text>
        </View>

        <View style={styles.infoBox}>
          <Text
            style={[styles.placeName, { color: theme.colors.textPrimary }]}
            numberOfLines={1}
          >
            {destination.name}
          </Text>
          <Text
            style={[styles.addressText, { color: theme.colors.textSecondary }]}
            numberOfLines={2}
          >
            {destination.address}
          </Text>

          {/* Route Status / Info Badge */}
          {routeStatus === 'READY' && formattedDistance ? (
            <View style={styles.routeBadgeRow}>
              <View style={[styles.routeBadge, { backgroundColor: 'rgba(59, 130, 246, 0.15)' }]}>
                <Text style={[styles.routeBadgeText, { color: theme.colors.primary }]}>
                  🛣️ {formattedDistance} • Offline OSM Route
                </Text>
              </View>
            </View>
          ) : routeStatus === 'ERROR' ? (
            <Text style={styles.errorText}>
              ⚠️ {routeError === 'OUTSIDE_OFFLINE_COVERAGE'
                ? 'Outside installed offline map bounds'
                : routeError === 'NO_START_ROAD'
                ? 'No road found near vehicle position'
                : routeError === 'NO_DESTINATION_ROAD'
                ? 'No road found near destination'
                : 'No connected offline route found'}
            </Text>
          ) : (
            <Text style={[styles.coordText, { color: theme.colors.textMuted }]}>
              {destination.latitude.toFixed(5)}° N, {destination.longitude.toFixed(5)}° E
            </Text>
          )}
        </View>

        <TouchableOpacity onPress={onCancel} style={styles.closeBtn} activeOpacity={0.7}>
          <Text style={[styles.closeIcon, { color: theme.colors.textSecondary }]}>✕</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.actionsRow}>
        <TouchableOpacity
          style={[
            styles.startBtn,
            {
              backgroundColor:
                routeStatus === 'CALCULATING' ? theme.colors.cardBorder : theme.colors.primary,
            },
          ]}
          onPress={onStartNavigation}
          disabled={routeStatus === 'CALCULATING'}
          activeOpacity={0.8}
        >
          {routeStatus === 'CALCULATING' ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator size="small" color="#FFFFFF" style={{ marginRight: 8 }} />
              <Text style={styles.startBtnText}>CALCULATING ROUTE...</Text>
            </View>
          ) : (
            <Text style={styles.startBtnText}>START NAVIGATION</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.changeBtn, { borderColor: theme.colors.cardBorder }]}
          onPress={onCancel}
          activeOpacity={0.8}
        >
          <Text style={[styles.changeBtnText, { color: theme.colors.textSecondary }]}>
            CANCEL
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 16,
    left: 14,
    right: 14,
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
    elevation: 10,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    zIndex: 35,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  destIcon: {
    fontSize: 18,
  },
  infoBox: {
    flex: 1,
    marginRight: 8,
  },
  placeName: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.3,
    marginBottom: 2,
  },
  addressText: {
    fontSize: 12,
    fontWeight: '500',
    lineHeight: 16,
    marginBottom: 4,
  },
  coordText: {
    fontSize: 10,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  routeBadgeRow: {
    flexDirection: 'row',
    marginTop: 2,
    marginBottom: 4,
  },
  routeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  routeBadgeText: {
    fontSize: 11,
    fontWeight: '800',
  },
  errorText: {
    color: '#EF4444',
    fontSize: 11,
    fontWeight: '700',
    marginTop: 2,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeIcon: {
    fontSize: 18,
    fontWeight: '700',
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  startBtn: {
    flex: 1,
    height: 44,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
  },
  startBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  changeBtn: {
    height: 44,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  changeBtnText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});
