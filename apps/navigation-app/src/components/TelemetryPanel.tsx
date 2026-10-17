import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useAppTheme } from '../theme/ThemeContext';
import { NavigationState } from '../types/navigation';
import { useNavigation } from '../state/NavigationContext';

interface TelemetryPanelProps {
  navState: NavigationState;
}

export const TelemetryPanel: React.FC<TelemetryPanelProps> = ({ navState }) => {
  const { startNavigation, startDemoNavigation, stopNavigation } = useNavigation();
  const { theme } = useAppTheme();

  const isNavigating = navState.isNavigating;
  const isSignalLost = navState.gnssStatus === 'SIGNAL_LOST';
  const isWaiting = navState.gnssStatus === 'WAITING' || navState.gnssStatus === 'PERMISSION_REQUIRED';

  const speedEst = navState.speedEstimate;
  const speedDisplay =
    isSignalLost || isWaiting || !speedEst || !speedEst.valid || speedEst.speedKmh === null
      ? '--'
      : speedEst.speedKmh.toFixed(1);

  const speedSourceTag =
    speedEst && speedEst.valid && speedEst.speedKmh !== null && speedEst.speedKmh > 0
      ? speedEst.source === 'GNSS_REPORTED'
        ? 'REP'
        : speedEst.source === 'GNSS_DERIVED'
        ? 'DER'
        : ''
      : '';

  const headingEst = navState.headingEstimate;
  const headingDisplay =
    isSignalLost || isWaiting || !headingEst || !headingEst.valid || headingEst.headingDeg === null
      ? '--'
      : `${Math.round(headingEst.headingDeg)}°`;

  const accuracyDisplay =
    isWaiting || navState.positionUncertainty === null
      ? '--'
      : isSignalLost
      ? `Last ${navState.positionUncertainty.toFixed(1)} m`
      : `${navState.positionUncertainty.toFixed(1)} m`;

  return (
    <View style={[styles.panel, { backgroundColor: theme.colors.card, borderTopColor: theme.colors.cardBorder }]}>
      {/* Real GNSS Telemetry Strip */}
      <View style={[styles.strip, { backgroundColor: theme.colors.surfaceHeader, borderColor: theme.colors.cardBorder }]}>
        {/* SPEED */}
        <View style={styles.metricCell}>
          <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>
            SPEED {speedSourceTag ? `(${speedSourceTag})` : ''}
          </Text>
          <View style={styles.numRow}>
            <Text style={[styles.numValue, { color: theme.colors.textPrimary }]}>{speedDisplay}</Text>
            <Text style={[styles.numUnit, { color: theme.colors.textSecondary }]}>km/h</Text>
          </View>
        </View>

        <View style={[styles.vertDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* HEADING / GNSS COURSE */}
        <View style={styles.metricCell}>
          <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>GNSS COURSE</Text>
          <View style={styles.numRow}>
            <Text style={[styles.numValue, { color: theme.colors.textPrimary }]}>{headingDisplay}</Text>
          </View>
        </View>

        <View style={[styles.vertDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* ACCURACY */}
        <View style={styles.metricCell}>
          <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>ACCURACY</Text>
          <View style={styles.numRow}>
            <Text style={[styles.numValue, { color: theme.colors.textPrimary }]}>{accuracyDisplay}</Text>
          </View>
        </View>
      </View>

      {/* Action Button Row */}
      <View style={styles.actionRow}>
        {!isNavigating ? (
          <TouchableOpacity
            style={[styles.startBtn, { backgroundColor: theme.colors.primary }]}
            onPress={() => {
              console.log('[START_TRACE] TELEMETRY_PANEL_UI_CALLBACK');
              console.log('[DEMO_SESSION] START_REQUEST');
              startDemoNavigation();
            }}
            activeOpacity={0.85}
          >
            <Text style={styles.startBtnText}>START NAVIGATION</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.activeBtnGroup}>
            <View style={styles.statusIndicatorBox}>
              <View style={[styles.dot, styles.dotGreen]} />
              <Text style={[styles.statusIndicatorText, { color: theme.colors.textPrimary }]}>
                {navState.gnssStatus === 'SIGNAL_LOST'
                  ? 'GNSS SIGNAL LOST'
                  : navState.gnssStatus === 'WAITING'
                  ? 'WAITING FOR FIX'
                  : 'GNSS ACTIVE'}
              </Text>
            </View>

            <TouchableOpacity
              style={[styles.endBtn, { backgroundColor: theme.colors.secondaryButton, borderColor: theme.colors.cardBorder }]}
              onPress={stopNavigation}
              activeOpacity={0.8}
            >
              <Text style={styles.endBtnText}>END</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  panel: {
    paddingHorizontal: 12,
    paddingTop: 10,
    paddingBottom: 14,
    borderTopWidth: 1,
  },
  strip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 10,
  },
  metricCell: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  numRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  numValue: {
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.2,
  },
  numUnit: {
    fontSize: 10,
    fontWeight: '700',
    marginLeft: 3,
  },
  vertDivider: {
    width: 1,
    height: 24,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  startBtn: {
    flex: 1,
    height: 44,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  startBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 1.0,
  },
  activeBtnGroup: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusIndicatorBox: {
    flex: 1,
    height: 44,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  dotGreen: {
    backgroundColor: '#10B981',
  },
  statusIndicatorText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  endBtn: {
    width: 80,
    height: 44,
    borderRadius: 8,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  endBtnText: {
    color: '#EF4444',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
});
