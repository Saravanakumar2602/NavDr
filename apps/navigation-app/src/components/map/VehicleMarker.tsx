import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useAppTheme } from '../../theme/ThemeContext';

interface VehicleMarkerProps {
  heading: number;
  isDenied?: boolean;
}

export const VehicleMarker: React.FC<VehicleMarkerProps> = ({ heading, isDenied = false }) => {
  const { theme } = useAppTheme();

  const arrowColor = isDenied ? theme.colors.idrPath : theme.colors.vehicleMarker;
  const pulseBg = isDenied ? theme.colors.accuracyDrCircle : theme.colors.accuracyCircle;

  return (
    <View style={styles.container}>
      {/* Position Uncertainty Accuracy Halo */}
      <View style={[styles.halo, { backgroundColor: pulseBg, borderColor: arrowColor }]} />

      {/* Heading-Oriented Navigation Arrow */}
      <View style={[styles.arrowBox, { transform: [{ rotate: `${heading}deg` }] }]}>
        <View style={[styles.arrowHead, { borderBottomColor: arrowColor }]} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
  halo: {
    position: 'absolute',
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
  },
  arrowBox: {
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrowHead: {
    width: 0,
    height: 0,
    borderLeftWidth: 6,
    borderRightWidth: 6,
    borderBottomWidth: 15,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
  },
});
