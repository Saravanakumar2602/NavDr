import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useAppTheme } from '../theme/ThemeContext';
import { useNavigation } from '../state/NavigationContext';
import { IMUMotionNoisePanel } from '../components/IMUMotionNoisePanel';

export const SystemStatusScreen: React.FC = () => {

  const { state } = useNavigation();
  const { theme } = useAppTheme();
  const diag = state.diagnostics;

  const isGnssAvailable = state.gnssStatus === 'AVAILABLE';
  const hasFix = state.currentFix !== null;

  const latDisplay = hasFix ? `${state.pose.latitude.toFixed(6)}° N` : 'WAITING FOR FIX';
  const lngDisplay = hasFix ? `${state.pose.longitude.toFixed(6)}° E` : 'WAITING FOR FIX';
  const altDisplay =
    state.currentFix?.altitude !== null && state.currentFix?.altitude !== undefined
      ? `${Math.round(state.currentFix.altitude)} m`
      : '--';

  const currentAccDisplay =
    diag.currentAccuracy !== null ? `${diag.currentAccuracy.toFixed(1)} m` : '--';
  const minAccDisplay = diag.minAccuracy !== null ? `${diag.minAccuracy.toFixed(1)} m` : '--';
  const maxAccDisplay = diag.maxAccuracy !== null ? `${diag.maxAccuracy.toFixed(1)} m` : '--';
  const meanAccDisplay = diag.meanAccuracy !== null ? `${diag.meanAccuracy.toFixed(1)} m` : '--';

  const reportedSpeedDisplay =
    diag.reportedSpeedKmH !== null ? `${diag.reportedSpeedKmH.toFixed(1)} km/h` : '--';
  const derivedSpeedDisplay =
    diag.derivedSpeedKmH !== null ? `${diag.derivedSpeedKmH.toFixed(1)} km/h` : '--';
  const courseDisplay = diag.reportedBearing !== null ? `${diag.reportedBearing}°` : '--';

  const updateRateDisplay = `${state.updateRateHz.toFixed(2)} Hz`;
  const intervalDisplay =
    diag.medianIntervalMs > 0
      ? `${diag.medianIntervalMs} ms (${diag.minIntervalMs}-${diag.maxIntervalMs} ms)`
      : '--';

  const statusLabel =
    state.gnssStatus === 'AVAILABLE'
      ? 'FIX AVAILABLE'
      : state.gnssStatus === 'PERMISSION_REQUIRED'
      ? 'PERMISSION DENIED'
      : state.gnssStatus === 'SIGNAL_LOST'
      ? 'FIX STALE (SIGNAL LOST)'
      : 'NO FIX (WAITING)';

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* Title */}
      <View style={styles.titleSection}>
        <Text style={[styles.sectionHeader, { color: theme.colors.primary }]}>
          REAL GNSS DIAGNOSTICS & TELEMETRY
        </Text>
        <Text style={[styles.pageTitle, { color: theme.colors.textPrimary }]}>System Status</Text>
      </View>

      {/* REAL GNSS LOCATION TELEMETRY SECTION */}
      <View
        style={[
          styles.sectionGroup,
          { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder },
        ]}
      >
        <Text style={[styles.groupTitle, { color: theme.colors.textSecondary }]}>
          REAL PHONE LOCATION DIAGNOSTICS
        </Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* STATUS */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>GNSS Status</Text>
          <View style={styles.statusBadgeRow}>
            <View
              style={[
                styles.dot,
                state.gnssStatus === 'AVAILABLE'
                  ? styles.dotGreen
                  : state.gnssStatus === 'SIGNAL_LOST'
                  ? styles.dotRed
                  : styles.dotAmber,
              ]}
            />
            <Text
              style={[
                styles.statusText,
                state.gnssStatus === 'AVAILABLE'
                  ? styles.textGreen
                  : state.gnssStatus === 'SIGNAL_LOST'
                  ? styles.textRed
                  : styles.textAmber,
              ]}
            >
              {statusLabel}
            </Text>
          </View>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* FIX AGE & COUNT */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>
            Fix Age / Total Fixes
          </Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {diag.lastFixAgeSeconds.toFixed(1)} s • {diag.fixCount} fixes
          </Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* UPDATE RATE & INTERVAL */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Update Rate</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {updateRateDisplay}
          </Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>Fix Interval (Median / Range)</Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>{intervalDisplay}</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* LATITUDE & LONGITUDE */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Latitude / Longitude</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {latDisplay}
          </Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>Longitude</Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>{lngDisplay}</Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>Altitude</Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>{altDisplay}</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* ACCURACY BREAKDOWN */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Current Accuracy</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {currentAccDisplay}
          </Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>
            Accuracy (Min / Mean / Max)
          </Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>
            {minAccDisplay} / {meanAccDisplay} / {maxAccDisplay}
          </Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* SPEED AUDIT (REPORTED VS DERIVED) */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Reported Speed</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {reportedSpeedDisplay} {diag.hasSpeed ? '(Valid)' : '(Unavailable)'}
          </Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>Derived Speed (Δd / Δt)</Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>
            {derivedSpeedDisplay}
          </Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* COURSE / BEARING AUDIT */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>GNSS Course</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {courseDisplay} {diag.hasBearing ? '(Valid)' : '(Unavailable)'}
          </Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* POSITION JITTER (STATIONARY DISPLACEMENT) */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Raw Position Jitter</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            Max {diag.rawJitterMaxMeters} m
          </Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>Mean Raw Displacement</Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>
            {diag.rawJitterMeanMeters} m
          </Text>
        </View>
      </View>

      {/* GNSS FILTER TELEMETRY SECTION (STAGE B.2) */}
      <View
        style={[
          styles.sectionGroup,
          { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder },
        ]}
      >
        <Text style={[styles.groupTitle, { color: theme.colors.primary }]}>GNSS FILTER TELEMETRY (STAGE B.2)</Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* FILTER STATE */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Filter Mode State</Text>
          <View style={styles.statusBadgeRow}>
            <View
              style={[
                styles.dot,
                diag.filterState === 'MOVING'
                  ? styles.dotGreen
                  : diag.filterState === 'OUTLIER_REJECTED'
                  ? styles.dotRed
                  : styles.dotAmber,
              ]}
            />
            <Text
              style={[
                styles.statusText,
                diag.filterState === 'MOVING'
                  ? styles.textGreen
                  : diag.filterState === 'OUTLIER_REJECTED'
                  ? styles.textRed
                  : styles.textAmber,
              ]}
            >
              {diag.filterState}
            </Text>
          </View>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* ACCEPTED / REJECTED FIXES */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Accepted Fixes / Outliers</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {diag.acceptedFixCount} Accepted • {diag.rejectedOutlierCount} Rejected
          </Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* FILTERED SPEED */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Filtered Speed</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {diag.filteredSpeedKmH !== null ? `${diag.filteredSpeedKmH.toFixed(1)} km/h` : '--'}
          </Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* FILTERED HEADING */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Filtered Course / Heading</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            {diag.filteredHeadingDeg !== null ? `${diag.filteredHeadingDeg}°` : '--'}
          </Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        {/* FILTERED POSITION JITTER */}
        <View style={styles.rowItem}>
          <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Filtered Position Jitter</Text>
          <Text style={[styles.valText, { color: theme.colors.textPrimary }]}>
            Max {diag.filteredJitterMaxMeters} m
          </Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>Mean Filtered Displacement</Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>
            {diag.filteredJitterMeanMeters} m
          </Text>
        </View>
        <View style={styles.subRowItem}>
          <Text style={[styles.itemSubText, { color: theme.colors.textMuted }]}>Filter Execution Latency</Text>
          <Text style={[styles.valSubText, { color: theme.colors.textSecondary }]}>
            {diag.filterLatencyMs.toFixed(2)} ms
          </Text>
        </View>
      </View>

      {/* SMARTPHONE IMU MOTION & SENSOR NOISE VISUAL PANEL */}
      <IMUMotionNoisePanel />

      {/* HARDWARE SUBSYSTEMS SECTION */}
      <View
        style={[
          styles.sectionGroup,
          { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder },
        ]}
      >

        <Text style={[styles.groupTitle, { color: theme.colors.textSecondary }]}>HARDWARE SUBSYSTEMS</Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.rowItem}>
          <View>
            <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>GNSS Receiver</Text>
            <Text style={[styles.itemSub, { color: theme.colors.textMuted }]}>Android Location Provider</Text>
          </View>
          <View style={styles.statusBadgeRow}>
            <View style={[styles.dot, isGnssAvailable ? styles.dotGreen : styles.dotAmber]} />
            <Text style={[styles.statusText, isGnssAvailable ? styles.textGreen : styles.textAmber]}>
              {isGnssAvailable ? 'Active' : 'Standby'}
            </Text>
          </View>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.rowItem}>
          <View>
            <Text style={[styles.itemTitle, { color: theme.colors.textPrimary }]}>Map Engine</Text>
            <Text style={[styles.itemSub, { color: theme.colors.textMuted }]}>MapLibre GL Native</Text>
          </View>
          <View style={styles.statusBadgeRow}>
            <View style={[styles.dot, styles.dotGreen]} />
            <Text style={[styles.statusText, styles.textGreen]}>Ready</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 28,
  },
  titleSection: {
    marginBottom: 16,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  pageTitle: {
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  sectionGroup: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 14,
    marginBottom: 14,
  },
  groupTitle: {
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  ruleDivider: {
    height: 1,
    marginTop: 8,
    marginBottom: 12,
  },
  rowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  subRowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 6,
    paddingLeft: 8,
  },
  rowDivider: {
    height: 1,
    marginVertical: 2,
  },
  itemTitle: {
    fontSize: 13,
    fontWeight: '700',
  },
  itemSub: {
    fontSize: 10,
    marginTop: 1,
  },
  itemSubText: {
    fontSize: 11,
    fontWeight: '600',
  },
  valText: {
    fontSize: 13,
    fontWeight: '800',
    fontVariant: ['tabular-nums'],
  },
  valSubText: {
    fontSize: 11,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  statusBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    marginRight: 6,
  },
  dotGreen: {
    backgroundColor: '#10B981',
  },
  dotAmber: {
    backgroundColor: '#F59E0B',
  },
  dotRed: {
    backgroundColor: '#EF4444',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '800',
  },
  textGreen: {
    color: '#10B981',
  },
  textAmber: {
    color: '#F59E0B',
  },
  textRed: {
    color: '#EF4444',
  },
});
