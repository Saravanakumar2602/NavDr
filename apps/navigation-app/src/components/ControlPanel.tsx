import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useNavigation } from '../state/NavigationContext';
import { theme } from '../theme/theme';

export const ControlPanel: React.FC = () => {
  const { state, startNavigation, stopNavigation } = useNavigation();

  const isNavigating = state.isNavigating;
  const demoIndex = state.demoStateIndex ?? 0;

  const demoStateLabels = ['1. GNSS AVAILABLE', '2. GNSS DENIED (IDR)', '3. RECOVERING (FUSION)'];

  return (
    <View style={styles.container}>
      {/* Primary Navigation Toggle Button */}
      <TouchableOpacity
        style={[
          styles.mainButton,
          isNavigating ? styles.mainButtonStop : styles.mainButtonStart,
        ]}
        onPress={isNavigating ? stopNavigation : startNavigation}
        activeOpacity={0.8}
      >
        <Text style={[styles.mainButtonText, isNavigating && styles.stopButtonText]}>
          {isNavigating ? 'STOP NAVIGATION' : 'START NAVIGATION'}
        </Text>
      </TouchableOpacity>

      {/* Secondary Demo Controls Row */}
      <View style={styles.secondaryRow}>
        <View style={styles.demoStateButton}>
          <Text style={styles.demoStateLabel}>NAVIGATION MODE:</Text>
          <Text style={styles.demoStateValue}>{state.navigationMode}</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 4,
  },
  mainButton: {
    paddingVertical: 14,
    borderRadius: theme.borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
    shadowColor: theme.colors.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  mainButtonStart: {
    backgroundColor: theme.colors.primaryButton,
  },
  mainButtonStop: {
    backgroundColor: theme.colors.outageButton,
  },
  mainButtonText: {
    fontSize: 15,
    fontWeight: '800',
    color: theme.colors.primaryButtonText,
    letterSpacing: 1.2,
  },
  stopButtonText: {
    color: theme.colors.outageButtonText,
  },

  secondaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  demoStateButton: {
    flex: 1,
    backgroundColor: theme.colors.secondaryButton,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    borderRadius: theme.borderRadius.sm,
    paddingHorizontal: 10,
    paddingVertical: 8,
    marginRight: 8,
    justifyContent: 'center',
  },
  demoStateLabel: {
    fontSize: 8,
    fontWeight: '700',
    color: theme.colors.textMuted,
    letterSpacing: 0.5,
  },
  demoStateValue: {
    fontSize: 10,
    fontWeight: '800',
    color: theme.colors.accent,
    marginTop: 1,
  },
  resetButton: {
    backgroundColor: theme.colors.secondaryButton,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    borderRadius: theme.borderRadius.sm,
    paddingHorizontal: 14,
    paddingVertical: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  resetText: {
    fontSize: 10,
    fontWeight: '800',
    color: theme.colors.textSecondary,
    letterSpacing: 0.8,
  },
});
