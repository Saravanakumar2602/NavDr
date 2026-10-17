import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '../theme/theme';

interface IMUMotionNoisePanelProps {
  timeSec?: number;
  accelX?: number;
  accelY?: number;
  accelZ?: number;
  gyroX?: number;
  gyroY?: number;
  gyroZ?: number;
}

export const IMUMotionNoisePanel: React.FC<IMUMotionNoisePanelProps> = ({
  timeSec = 0,
  accelX = 0.12,
  accelY = -0.05,
  accelZ = 9.81,
  gyroX = 0.01,
  gyroY = -0.02,
  gyroZ = 0.03,
}) => {
  return (
    <View style={styles.container}>
      {/* Panel Header */}
      <View style={styles.header}>
        <Text style={styles.title}>SMARTPHONE IMU MOTION & NOISE PIPELINE</Text>
        <Text style={styles.subTitle}>6-DoF Sensor Dynamics vs Real-World Vehicle Noise</Text>
      </View>

      {/* 6 Channel Grid */}
      <View style={styles.grid}>
        {/* Accel X */}
        <View style={styles.channelCard}>
          <Text style={[styles.channelName, { color: '#38BDF8' }]}>ACCEL X (Longitudinal)</Text>
          <Text style={[styles.channelVal, { color: '#38BDF8' }]}>{accelX.toFixed(2)} m/s²</Text>
          <View style={styles.badgeBox}>
            <Text style={[styles.badgeText, { color: '#FB923C' }]}>BRAKING / ACCEL</Text>
          </View>
        </View>

        {/* Gyro X */}
        <View style={styles.channelCard}>
          <Text style={[styles.channelName, { color: '#FBBF24' }]}>GYRO X (Roll Rate)</Text>
          <Text style={[styles.channelVal, { color: '#FBBF24' }]}>{gyroX.toFixed(3)} rad/s</Text>
          <View style={styles.badgeBox}>
            <Text style={[styles.badgeText, { color: '#38BDF8' }]}>SENSOR NOISE</Text>
          </View>
        </View>

        {/* Accel Y */}
        <View style={styles.channelCard}>
          <Text style={[styles.channelName, { color: '#818CF8' }]}>ACCEL Y (Lateral)</Text>
          <Text style={[styles.channelVal, { color: '#818CF8' }]}>{accelY.toFixed(2)} m/s²</Text>
          <View style={styles.badgeBox}>
            <Text style={[styles.badgeText, { color: '#C084FC' }]}>CORNERING FORCE</Text>
          </View>
        </View>

        {/* Gyro Y */}
        <View style={styles.channelCard}>
          <Text style={[styles.channelName, { color: '#FB7185' }]}>GYRO Y (Pitch Rate)</Text>
          <Text style={[styles.channelVal, { color: '#FB7185' }]}>{gyroY.toFixed(3)} rad/s</Text>
          <View style={styles.badgeBox}>
            <Text style={[styles.badgeText, { color: '#F87171' }]}>ROAD ROUGHNESS</Text>
          </View>
        </View>

        {/* Accel Z */}
        <View style={styles.channelCard}>
          <Text style={[styles.channelName, { color: '#34D399' }]}>ACCEL Z (Vertical + G)</Text>
          <Text style={[styles.channelVal, { color: '#34D399' }]}>{accelZ.toFixed(2)} m/s²</Text>
          <View style={styles.badgeBox}>
            <Text style={[styles.badgeText, { color: '#F87171' }]}>ENGINE VIBRATION</Text>
          </View>
        </View>

        {/* Gyro Z */}
        <View style={styles.channelCard}>
          <Text style={[styles.channelName, { color: '#A78BFA' }]}>GYRO Z (Yaw Rate)</Text>
          <Text style={[styles.channelVal, { color: '#A78BFA' }]}>{gyroZ.toFixed(3)} rad/s</Text>
          <View style={styles.badgeBox}>
            <Text style={[styles.badgeText, { color: '#C084FC' }]}>TURNING YAW</Text>
          </View>
        </View>
      </View>

      {/* Flow Card Below */}
      <View style={styles.flowCard}>
        <Text style={styles.flowText}>
          Smartphone IMU  ➔  Initial Motion Model (SpeedNet / EKF)  ➔  Speed / Motion Estimate
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#0B0F19',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1F293D',
    padding: 14,
    marginVertical: 8,
  },
  header: {
    marginBottom: 12,
  },
  title: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  subTitle: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  channelCard: {
    width: '48%',
    backgroundColor: '#111827',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1F293D',
    padding: 10,
    marginBottom: 4,
  },
  channelName: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  channelVal: {
    fontSize: 14,
    fontWeight: '900',
    marginTop: 4,
    fontFamily: 'Courier',
  },
  badgeBox: {
    marginTop: 6,
    backgroundColor: '#1E293B',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  flowCard: {
    marginTop: 10,
    backgroundColor: '#151D2A',
    borderColor: '#334155',
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
  },
  flowText: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
});
