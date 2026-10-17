import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useAppTheme } from '../../theme/ThemeContext';

interface MapControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRecenter: () => void;
  isFollowing?: boolean;
  hasValidPosition?: boolean;
}

export const MapControls: React.FC<MapControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onRecenter,
  isFollowing = true,
  hasValidPosition = true,
}) => {
  const { theme } = useAppTheme();

  return (
    <View
      style={styles.container}
      onTouchStart={(e) => e.stopPropagation()}
      onTouchEnd={(e) => e.stopPropagation()}
    >
      {/* Zoom In (+) Control Button */}
      <TouchableOpacity
        style={[
          styles.btn,
          {
            backgroundColor: theme.colors.card,
            borderColor: theme.colors.cardBorder,
          },
        ]}
        onPress={onZoomIn}
        activeOpacity={0.75}
        accessibilityLabel="Zoom map in"
        accessibilityRole="button"
      >
        <Text style={[styles.btnText, { color: theme.colors.textPrimary }]}>+</Text>
      </TouchableOpacity>

      {/* Zoom Out (−) Control Button */}
      <TouchableOpacity
        style={[
          styles.btn,
          {
            backgroundColor: theme.colors.card,
            borderColor: theme.colors.cardBorder,
          },
        ]}
        onPress={onZoomOut}
        activeOpacity={0.75}
        accessibilityLabel="Zoom map out"
        accessibilityRole="button"
      >
        <Text style={[styles.btnText, { color: theme.colors.textPrimary }]}>−</Text>
      </TouchableOpacity>

      {/* Recenter / Camera Follow Control Button */}
      <TouchableOpacity
        style={[
          styles.recenterBtn,
          {
            backgroundColor: !isFollowing ? theme.colors.primary : theme.colors.card,
            borderColor: !isFollowing ? theme.colors.primary : theme.colors.cardBorder,
            opacity: hasValidPosition ? 1.0 : 0.45,
          },
        ]}
        onPress={onRecenter}
        disabled={!hasValidPosition}
        activeOpacity={0.75}
        accessibilityLabel={!isFollowing ? 'Recenter map to vehicle' : 'Map following vehicle'}
        accessibilityRole="button"
      >
        {!isFollowing ? (
          <View style={styles.recenterContent}>
            <View style={styles.crosshairDot} />
            <Text style={styles.recenterText}>RECENTER</Text>
          </View>
        ) : (
          <View style={[styles.targetRing, { borderColor: theme.colors.primary }]}>
            <View style={[styles.targetDot, { backgroundColor: theme.colors.primary }]} />
          </View>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 24,
    right: 14,
    zIndex: 20,
    alignItems: 'flex-end',
  },
  btn: {
    width: 42,
    height: 42,
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    elevation: 4,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
  },
  btnText: {
    fontSize: 22,
    fontWeight: '700',
    includeFontPadding: false,
    textAlignVertical: 'center',
  },
  recenterBtn: {
    height: 42,
    minWidth: 42,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
    elevation: 4,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
  },
  recenterContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  crosshairDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#FFFFFF',
    marginRight: 6,
  },
  recenterText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  targetRing: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  targetDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
});

