import React from 'react';
import { View, StyleSheet, Text } from 'react-native';

interface DestinationMarkerProps {
  name?: string;
}

export const DestinationMarker: React.FC<DestinationMarkerProps> = () => {
  return (
    <View style={styles.container}>
      {/* Outer Pulse / Halo Ring */}
      <View style={styles.pulseRing} />

      {/* Pin Body */}
      <View style={styles.pinBody}>
        <View style={styles.pinCenterDot} />
      </View>

      {/* Pin Needle / Point */}
      <View style={styles.pinPointer} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: 36,
    height: 44,
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  pulseRing: {
    position: 'absolute',
    top: 4,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(239, 68, 68, 0.25)',
  },
  pinBody: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#EF4444', // Red / Crimson
    borderWidth: 2.5,
    borderColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 6,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 4,
  },
  pinCenterDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#FFFFFF',
  },
  pinPointer: {
    width: 0,
    height: 0,
    borderLeftWidth: 5,
    borderRightWidth: 5,
    borderTopWidth: 8,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: '#EF4444',
    marginTop: -1,
  },
});
