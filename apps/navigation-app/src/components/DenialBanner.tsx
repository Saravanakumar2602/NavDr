import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { GnssStatus } from '../types/navigation';
import { theme } from '../theme/theme';

interface DenialBannerProps {
  status: GnssStatus;
  message: string | null;
}

export const DenialBanner: React.FC<DenialBannerProps> = ({ status, message }) => {
  if (status === 'AVAILABLE' || !message) return null;

  const isDenied = status === 'DENIED';
  const bannerColor = isDenied ? theme.colors.gnssDenied : theme.colors.gnssRecovering;

  return (
    <View style={[styles.container, { borderColor: bannerColor }]}>
      <View style={[styles.indicatorDot, { backgroundColor: bannerColor }]} />
      <Text style={[styles.bannerText, { color: bannerColor }]}>
        {message}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(15, 22, 38, 0.95)',
    borderWidth: 1.5,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginHorizontal: 16,
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 5,
  },
  indicatorDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  bannerText: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
    flex: 1,
  },
});
