import React from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { useAppTheme } from '../theme/ThemeContext';

interface LogoProps {
  size?: number;
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ size = 26, showText = false }) => {
  const { theme } = useAppTheme();
  const innerSize = size * 0.45;

  return (
    <View style={styles.outerRow}>
      <View style={[styles.container, { width: size, height: size }]}>
        {/* Navigation Ring */}
        <View
          style={[
            styles.orbitRing,
            {
              width: size,
              height: size,
              borderRadius: size / 2,
              borderColor: theme.colors.primary,
            },
          ]}
        />
        {/* Inner Ring */}
        <View
          style={[
            styles.innerRing,
            {
              width: size * 0.7,
              height: size * 0.7,
              borderRadius: (size * 0.7) / 2,
              borderColor: theme.colors.cardBorder,
            },
          ]}
        />

        {/* Directional Arrow Vector */}
        <View style={[styles.arrowContainer, { width: innerSize, height: innerSize }]}>
          <View style={[styles.arrowHead, { borderBottomColor: theme.colors.primary }]} />
        </View>
      </View>

      {showText && (
        <View style={styles.textContainer}>
          <Text style={[styles.brandTitle, { color: theme.colors.textPrimary }]}>NavDR</Text>
          <Text style={[styles.brandTagline, { color: theme.colors.primary }]}>
            Navigate Beyond GNSS
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  outerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  orbitRing: {
    position: 'absolute',
    borderWidth: 1.5,
  },
  innerRing: {
    position: 'absolute',
    borderWidth: 1,
  },
  arrowContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2,
  },
  arrowHead: {
    width: 0,
    height: 0,
    backgroundColor: 'transparent',
    borderStyle: 'solid',
    borderLeftWidth: 5,
    borderRightWidth: 5,
    borderBottomWidth: 12,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    transform: [{ translateY: -1 }],
  },
  textContainer: {
    marginLeft: 8,
  },
  brandTitle: {
    fontSize: 17,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  brandTagline: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.4,
    marginTop: -2,
  },
});
