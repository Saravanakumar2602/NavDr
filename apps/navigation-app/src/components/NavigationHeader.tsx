import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Logo } from './Logo';
import { theme } from '../theme/theme';

interface NavigationHeaderProps {
  activeTab: 'navigation' | 'system';
  onTabChange: (tab: 'navigation' | 'system') => void;
}

export const NavigationHeader: React.FC<NavigationHeaderProps> = ({
  activeTab,
  onTabChange,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.brandingRow}>
        <Logo size={32} />
        <View style={styles.titleColumn}>
          <View style={styles.titleBadgeRow}>
            <Text style={styles.brandTitle}>NAVDR</Text>
            <View style={styles.demoBadge}>
              <Text style={styles.demoBadgeText}>DEMO MODE</Text>
            </View>
          </View>
          <Text style={styles.subtitle}>GNSS-Fused Intelligent Navigation</Text>
        </View>
      </View>

      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'navigation' && styles.tabButtonActive]}
          onPress={() => onTabChange('navigation')}
          activeOpacity={0.8}
        >
          <Text style={[styles.tabText, activeTab === 'navigation' && styles.tabTextActive]}>
            NAVIGATE
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'system' && styles.tabButtonActive]}
          onPress={() => onTabChange('system')}
          activeOpacity={0.8}
        >
          <Text style={[styles.tabText, activeTab === 'system' && styles.tabTextActive]}>
            SYSTEM & BENCHMARK
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surfaceHeader,
    paddingTop: 12,
    paddingBottom: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.cardBorder,
  },
  brandingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  titleColumn: {
    marginLeft: 12,
    flex: 1,
  },
  titleBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  brandTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: theme.colors.textPrimary,
    letterSpacing: 1.5,
  },
  demoBadge: {
    backgroundColor: 'rgba(0, 229, 255, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(0, 229, 255, 0.4)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  demoBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: theme.colors.accent,
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: 11,
    color: theme.colors.textSecondary,
    marginTop: 1,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: theme.colors.card,
    borderRadius: 8,
    padding: 3,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 7,
    alignItems: 'center',
    borderRadius: 6,
  },
  tabButtonActive: {
    backgroundColor: theme.colors.cardBorder,
  },
  tabText: {
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.textMuted,
    letterSpacing: 0.8,
  },
  tabTextActive: {
    color: theme.colors.accent,
  },
});
