import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAppTheme } from '../theme/ThemeContext';
import { GnssStatus } from '../types/navigation';

interface OutageBannerProps {
  status: GnssStatus;
  outageSeconds?: number;
  confidence?: number;
  speed?: number | null;
  heading?: number | null;
  drState?: 'DR_INACTIVE' | 'DR_READY' | 'DR_ACTIVE';
}

export const OutageBanner: React.FC<OutageBannerProps> = ({ status, outageSeconds = 0, drState }) => {
  const { theme } = useAppTheme();
  if (status === 'AVAILABLE' && drState !== 'DR_ACTIVE') return null;

  const formatTimer = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getBannerConfig = () => {
    if (drState === 'DR_ACTIVE' || status === 'SIGNAL_LOST') {
      return {
        title: `GNSS UNAVAILABLE • DR ACTIVE (${formatTimer(outageSeconds)})`,
        sub: 'Real-time phone IMU 7-State ENU Kinematic Engine propagation',
        color: '#EF4444',
        bgColor: 'rgba(239, 68, 68, 0.12)',
        borderColor: 'rgba(239, 68, 68, 0.40)',
      };
    }

    switch (status) {
      case 'RECOVERING':
        return {
          title: 'GNSS RECOVERED',
          sub: 'GNSS signal restored • Continuing normal navigation',
          color: '#10B981',
          bgColor: 'rgba(16, 185, 129, 0.12)',
          borderColor: 'rgba(16, 185, 129, 0.40)',
        };
      case 'WAITING':
        return {
          title: 'WAITING FOR LOCATION',
          sub: 'Searching for GPS satellite signals...',
          color: '#3B82F6',
          bgColor: 'rgba(59, 130, 246, 0.08)',
          borderColor: 'rgba(59, 130, 246, 0.35)',
        };
      case 'PERMISSION_REQUIRED':
        return {
          title: 'LOCATION PERMISSION REQUIRED',
          sub: 'Enable location permission in settings to navigate',
          color: '#F59E0B',
          bgColor: 'rgba(245, 158, 11, 0.08)',
          borderColor: 'rgba(245, 158, 11, 0.35)',
        };
      default:
        return null;
    }
  };

  const config = getBannerConfig();
  if (!config) return null;

  return (
    <View
      style={[
        styles.banner,
        { backgroundColor: config.bgColor, borderBottomColor: config.borderColor },
      ]}
    >
      <View style={styles.leftCol}>
        <View style={styles.titleRow}>
          <View style={[styles.dot, { backgroundColor: config.color }]} />
          <Text style={[styles.mainText, { color: config.color }]}>{config.title}</Text>
        </View>
        <Text style={[styles.subText, { color: theme.colors.textSecondary }]}>{config.sub}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  banner: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    zIndex: 15,
  },
  leftCol: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    marginRight: 8,
  },
  mainText: {
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  subText: {
    fontSize: 11,
    marginTop: 2,
    fontWeight: '500',
  },
});
