import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { Logo } from './Logo';
import { useAppTheme } from '../theme/ThemeContext';

interface SplashScreenProps {
  onFinish: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  const { theme } = useAppTheme();
  const [progress] = useState(new Animated.Value(0));

  useEffect(() => {
    Animated.timing(progress, {
      toValue: 1,
      duration: 1200,
      useNativeDriver: false,
    }).start(() => {
      onFinish();
    });
  }, []);

  const widthInterpolate = progress.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.centerContent}>
        {/* NavDR Logo Node */}
        <Logo size={60} showText={false} />

        <Text style={[styles.title, { color: theme.colors.textPrimary }]}>NavDR</Text>
        <Text style={[styles.tagline, { color: theme.colors.primary }]}>Navigate Beyond GNSS</Text>

        {/* Minimal Progress Line */}
        <View style={[styles.progressTrack, { backgroundColor: theme.colors.cardBorder }]}>
          <Animated.View style={[styles.progressBar, { width: widthInterpolate, backgroundColor: theme.colors.primary }]} />
        </View>

        <Text style={[styles.subtext, { color: theme.colors.textMuted }]}>INITIALIZING NAVDR SENSOR ENGINE...</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 999,
  },
  centerContent: {
    alignItems: 'center',
  },
  title: {
    fontSize: 30,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginTop: 16,
  },
  tagline: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    marginTop: 4,
    marginBottom: 24,
  },
  progressTrack: {
    width: 130,
    height: 3,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 2,
  },
  subtext: {
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.8,
    marginTop: 12,
  },
});
