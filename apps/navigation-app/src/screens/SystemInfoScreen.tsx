import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { theme } from '../theme/theme';

export const SystemInfoScreen: React.FC = () => {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* App Header */}
      <View style={styles.card}>
        <Text style={styles.sectionHeader}>PRODUCT SPECIFICATION</Text>
        <Text style={styles.appTitle}>NavDR — Intelligent Dead Reckoning</Text>
        <Text style={styles.appSubtitle}>GNSS-Fused Intelligent Navigation System</Text>
        <Text style={styles.bodyText}>
          NavDR provides continuous high-precision vehicular positioning during prolonged GNSS denials
          by fusing raw smartphone MEMS sensors (Accelerometer, Gyroscope) with deep neural speed
          estimation and kinematic constraints.
        </Text>
      </View>

      {/* Core Technologies Grid */}
      <View style={styles.card}>
        <Text style={styles.sectionHeader}>CORE NAVIGATION TECHNOLOGIES</Text>
        
        <View style={styles.techItem}>
          <Text style={styles.techTitle}>• Smartphone IMU Sensor Engine</Text>
          <Text style={styles.techDesc}>High-rate (200 Hz) Accel & Gyro background acquisition with thread offloading.</Text>
        </View>

        <View style={styles.techItem}>
          <Text style={styles.techTitle}>• SpeedNet CNN + BiLSTM Neural Model</Text>
          <Text style={styles.techDesc}>Deep temporal neural network predicting forward vehicle speed from raw IMU windows.</Text>
        </View>

        <View style={styles.techItem}>
          <Text style={styles.techTitle}>• M029 Multi-Anchor Heading Architecture</Text>
          <Text style={styles.techDesc}>Causal pre-outage GNSS course vector latch + motion-gated zero-yaw constraint + neural rate fusion.</Text>
        </View>

        <View style={styles.techItem}>
          <Text style={styles.techTitle}>• 7-State Extended Kalman Filter (EKF)</Text>
          <Text style={styles.techDesc}>Combines position, velocity, heading, and gyro bias estimations.</Text>
        </View>

        <View style={styles.techItem}>
          <Text style={styles.techTitle}>• Kinematic Constraints (2D NHC & ZUPT)</Text>
          <Text style={styles.techDesc}>Suppresses lateral/vertical motion slip and fixes zero-velocity drift during vehicle stops.</Text>
        </View>

        <View style={styles.techItem}>
          <Text style={styles.techTitle}>• Jerk-Based Adaptive Motion Processing (APM)</Text>
          <Text style={styles.techDesc}>Detects deceleration events to dynamically attenuate neural speed overestimation.</Text>
        </View>

        <View style={styles.techItem}>
          <Text style={styles.techTitle}>• Offline Map Matching (Planned)</Text>
          <Text style={styles.techDesc}>Local OpenStreetMap road network snapping engine for additional drift reduction.</Text>
        </View>
      </View>

      {/* Architecture Partitioning */}
      <View style={styles.card}>
        <Text style={styles.sectionHeader}>SYSTEM ARCHITECTURE</Text>
        <View style={styles.archRow}>
          <View style={styles.archBox}>
            <Text style={styles.archTitle}>CLOUD / DESKTOP</Text>
            <Text style={styles.archDesc}>Model Training, Dataset Curation, Hyperparameter Tuning</Text>
          </View>
          <View style={styles.archBox}>
            <Text style={styles.archTitle}>EDGE / SMARTPHONE</Text>
            <Text style={styles.archDesc}>Real-time Sensor Capture, SpeedNet Inference, EKF Fusion</Text>
          </View>
        </View>
      </View>

      {/* Benchmark Results Section */}
      <View style={[styles.card, styles.benchmarkCard]}>
        <View style={styles.benchmarkHeaderRow}>
          <Text style={styles.benchmarkTitle}>IO-VNBD BENCHMARK</Text>
          <View style={styles.datasetTag}>
            <Text style={styles.datasetTagText}>Benchmark dataset result</Text>
          </View>
        </View>

        <Text style={styles.benchmarkSub}>Canonical Vw04 Benchmark Dataset Performance (300 s Outage):</Text>

        <View style={styles.metricsGrid}>
          <View style={styles.metricCell}>
            <Text style={styles.metricLabel}>M028 BASELINE</Text>
            <Text style={styles.metricValueM028}>218.93 m</Text>
            <Text style={styles.metricSub}>@ 300 s Outage</Text>
          </View>

          <View style={styles.metricCell}>
            <Text style={styles.metricLabel}>M029 CANDIDATE</Text>
            <Text style={styles.metricValueM029}>48.20 m</Text>
            <Text style={styles.metricSub}>@ 300 s Outage</Text>
          </View>

          <View style={styles.metricCell}>
            <Text style={styles.metricLabel}>DRIFT REDUCTION</Text>
            <Text style={styles.metricValueGain}>77.98%</Text>
            <Text style={styles.metricSub}>Relative Improvement</Text>
          </View>
        </View>

        <View style={styles.disclaimerBox}>
          <Text style={styles.disclaimerText}>
            [DISCLAIMER] The 48.20 m error metric is a benchmark dataset result evaluated on the IO-VNBD Vw04 trajectory.
            Real smartphone live accuracy is subject to ongoing Stage 7 field validation.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    padding: 16,
  },
  card: {
    backgroundColor: theme.colors.card,
    borderRadius: theme.borderRadius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    padding: 14,
    marginBottom: 12,
  },
  sectionHeader: {
    fontSize: 9,
    fontWeight: '800',
    color: theme.colors.accent,
    letterSpacing: 1,
    marginBottom: 8,
  },
  appTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: theme.colors.textPrimary,
    marginBottom: 2,
  },
  appSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    color: theme.colors.textSecondary,
    marginBottom: 8,
  },
  bodyText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    lineHeight: 18,
  },
  techItem: {
    marginBottom: 8,
  },
  techTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  techDesc: {
    fontSize: 11,
    color: theme.colors.textSecondary,
    marginLeft: 10,
    marginTop: 1,
  },
  archRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  archBox: {
    width: '48%',
    backgroundColor: theme.colors.surfaceHeader,
    padding: 10,
    borderRadius: theme.borderRadius.sm,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  archTitle: {
    fontSize: 9,
    fontWeight: '800',
    color: theme.colors.accent,
    marginBottom: 4,
  },
  archDesc: {
    fontSize: 10,
    color: theme.colors.textSecondary,
    lineHeight: 14,
  },
  benchmarkCard: {
    borderColor: 'rgba(0, 229, 255, 0.4)',
  },
  benchmarkHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  benchmarkTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: theme.colors.textPrimary,
    letterSpacing: 0.8,
  },
  datasetTag: {
    backgroundColor: 'rgba(0, 229, 255, 0.15)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  datasetTagText: {
    fontSize: 9,
    fontWeight: '700',
    color: theme.colors.accent,
  },
  benchmarkSub: {
    fontSize: 11,
    color: theme.colors.textSecondary,
    marginBottom: 10,
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  metricCell: {
    width: '31%',
    backgroundColor: theme.colors.surfaceHeader,
    padding: 8,
    borderRadius: theme.borderRadius.sm,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 8,
    fontWeight: '700',
    color: theme.colors.textMuted,
  },
  metricValueM028: {
    fontSize: 13,
    fontWeight: '800',
    color: theme.colors.gnssDenied,
    marginVertical: 2,
  },
  metricValueM029: {
    fontSize: 13,
    fontWeight: '800',
    color: theme.colors.gnssHealthy,
    marginVertical: 2,
  },
  metricValueGain: {
    fontSize: 13,
    fontWeight: '800',
    color: theme.colors.accent,
    marginVertical: 2,
  },
  metricSub: {
    fontSize: 8,
    color: theme.colors.textMuted,
  },
  disclaimerBox: {
    backgroundColor: 'rgba(255, 171, 0, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 171, 0, 0.3)',
    borderRadius: 6,
    padding: 8,
  },
  disclaimerText: {
    fontSize: 9,
    color: theme.colors.gnssRecovering,
    lineHeight: 13,
  },
});
