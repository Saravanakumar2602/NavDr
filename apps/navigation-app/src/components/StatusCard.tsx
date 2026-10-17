import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { NavigationState } from '../types/navigation';
import { theme } from '../theme/theme';

interface StatusCardProps {
  navState: NavigationState;
}

export const StatusCard: React.FC<StatusCardProps> = ({ navState }) => {
  const { gnssStatus, navigationMode, imuStatus, mapStatus, pose, positionUncertainty } = navState;

  const getGnssColor = () => {
    switch (gnssStatus) {
      case 'AVAILABLE':
        return theme.colors.gnssHealthy;
      case 'DENIED':
        return theme.colors.gnssDenied;
      case 'RECOVERING':
        return theme.colors.gnssRecovering;
      default:
        return theme.colors.textMuted;
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.grid}>
        {/* Row 1: GNSS Status & Navigation Mode */}
        <View style={styles.cardItem}>
          <Text style={styles.label}>GNSS STATUS</Text>
          <View style={styles.statusRow}>
            <View style={[styles.statusDot, { backgroundColor: getGnssColor() }]} />
            <Text style={[styles.valueBold, { color: getGnssColor() }]}>{gnssStatus}</Text>
          </View>
        </View>

        <View style={styles.cardItem}>
          <Text style={styles.label}>NAVIGATION MODE</Text>
          <Text style={[styles.valueBold, { color: theme.colors.accent }]}>
            {navigationMode}
          </Text>
        </View>

        {/* Row 2: Speed & Heading */}
        <View style={styles.cardItem}>
          <Text style={styles.label}>VEHICLE SPEED</Text>
          <Text style={styles.valueLarge}>
            {pose.speed !== null && pose.speed !== undefined ? pose.speed.toFixed(1) : '--'}{' '}
            <Text style={styles.unitText}>km/h</Text>
          </Text>
        </View>

        <View style={styles.cardItem}>
          <Text style={styles.label}>HEADING ANCHOR</Text>
          <Text style={styles.valueLarge}>
            {pose.heading !== null && pose.heading !== undefined ? `${Math.round(pose.heading)}°` : '--'}
          </Text>
        </View>

        {/* Row 3: Subsystems & Uncertainty / DR Distance / Map Match */}
        <View style={styles.cardItemFull}>
          <View style={styles.subsystemRow}>
            <View style={styles.subsystemItem}>
              <Text style={styles.subLabel}>IMU</Text>
              <Text style={styles.subValue}>{imuStatus}</Text>
            </View>
            <View style={styles.subsystemDivider} />
            <View style={styles.subsystemItem}>
              <Text style={styles.subLabel}>
                {navState.drState === 'DR_ACTIVE' ? 'MAP MATCH' : 'MAP'}
              </Text>
              <Text style={styles.subValue}>
                {navState.drState === 'DR_ACTIVE'
                  ? (navState.mapMatchStatus || 'UNAVAILABLE')
                  : mapStatus}
              </Text>
            </View>
            <View style={styles.subsystemDivider} />
            <View style={styles.subsystemItem}>
              <Text style={styles.subLabel}>
                {navState.drState === 'DR_ACTIVE' ? 'DR TRAJ DIST' : 'UNCERTAINTY'}
              </Text>
              <Text style={styles.subValueHighlight}>
                {navState.drState === 'DR_ACTIVE' && navState.drDistanceMeters !== undefined
                  ? `${navState.drDistanceMeters.toFixed(1)} m`
                  : positionUncertainty !== null ? `±${positionUncertainty.toFixed(1)} m` : '--'}
              </Text>
            </View>
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  cardItem: {
    width: '48.5%',
    backgroundColor: theme.colors.card,
    borderRadius: theme.borderRadius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    padding: 10,
    marginBottom: 8,
  },
  cardItemFull: {
    width: '100%',
    backgroundColor: theme.colors.card,
    borderRadius: theme.borderRadius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    padding: 10,
  },
  label: {
    fontSize: 9,
    fontWeight: '700',
    color: theme.colors.textMuted,
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    marginRight: 6,
  },
  valueBold: {
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  valueLarge: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.colors.textPrimary,
  },
  unitText: {
    fontSize: 11,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  subsystemRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  subsystemItem: {
    alignItems: 'center',
  },
  subsystemDivider: {
    width: 1,
    height: 18,
    backgroundColor: theme.colors.cardBorder,
  },
  subLabel: {
    fontSize: 8,
    fontWeight: '700',
    color: theme.colors.textMuted,
    letterSpacing: 0.5,
  },
  subValue: {
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    marginTop: 1,
  },
  subValueHighlight: {
    fontSize: 11,
    fontWeight: '800',
    color: theme.colors.accent,
    marginTop: 1,
  },
});
