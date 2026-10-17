import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useAppTheme } from '../theme/ThemeContext';
import { ActiveTab } from '../types/navigation';

interface BottomNavBarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  bottomInset?: number;
}

export const BottomNavBar: React.FC<BottomNavBarProps> = ({
  activeTab,
  onTabChange,
  bottomInset = 0,
}) => {
  const { theme } = useAppTheme();

  const isNav = activeTab === 'NAVIGATE';
  const isSys = activeTab === 'SYSTEM';
  const isSet = activeTab === 'SETTINGS';

  const activeColor = theme.colors.primary;
  const inactiveColor = theme.colors.textMuted;

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.surfaceHeader,
          borderTopColor: theme.colors.cardBorder,
          paddingBottom: Math.max(bottomInset, 8),
        },
      ]}
    >
      {/* NAVIGATE Tab */}
      <TouchableOpacity
        style={styles.tabButton}
        onPress={() => onTabChange('NAVIGATE')}
        activeOpacity={0.7}
      >
        <View style={styles.iconBox}>
          <View style={[styles.navOuterRing, { borderColor: isNav ? activeColor : inactiveColor }]}>
            <View
              style={[
                styles.navArrowDelta,
                { borderBottomColor: isNav ? activeColor : inactiveColor },
              ]}
            />
          </View>
        </View>
        <Text style={[styles.tabLabel, { color: isNav ? activeColor : inactiveColor }]}>
          Navigate
        </Text>
      </TouchableOpacity>

      {/* SYSTEM Tab */}
      <TouchableOpacity
        style={styles.tabButton}
        onPress={() => onTabChange('SYSTEM')}
        activeOpacity={0.7}
      >
        <View style={styles.iconBox}>
          <View style={[styles.sysSquare, { borderColor: isSys ? activeColor : inactiveColor }]}>
            <View style={[styles.sysLine, { backgroundColor: isSys ? activeColor : inactiveColor }]} />
            <View style={[styles.sysLine, { backgroundColor: isSys ? activeColor : inactiveColor }]} />
          </View>
        </View>
        <Text style={[styles.tabLabel, { color: isSys ? activeColor : inactiveColor }]}>
          System
        </Text>
      </TouchableOpacity>

      {/* SETTINGS Tab */}
      <TouchableOpacity
        style={styles.tabButton}
        onPress={() => onTabChange('SETTINGS')}
        activeOpacity={0.7}
      >
        <View style={styles.iconBox}>
          <View style={[styles.setSlidersOutline, { borderColor: isSet ? activeColor : inactiveColor }]}>
            <View style={[styles.setDot1, { backgroundColor: isSet ? activeColor : inactiveColor }]} />
            <View style={[styles.setDot2, { backgroundColor: isSet ? activeColor : inactiveColor }]} />
          </View>
        </View>
        <Text style={[styles.tabLabel, { color: isSet ? activeColor : inactiveColor }]}>
          Settings
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    borderTopWidth: 1,
    paddingTop: 8,
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBox: {
    width: 22,
    height: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  navOuterRing: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  navArrowDelta: {
    width: 0,
    height: 0,
    borderLeftWidth: 3.5,
    borderRightWidth: 3.5,
    borderBottomWidth: 9,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    transform: [{ translateY: -1 }],
  },
  sysSquare: {
    width: 18,
    height: 18,
    borderRadius: 3,
    borderWidth: 1.8,
    justifyContent: 'space-evenly',
    alignItems: 'center',
    paddingVertical: 2,
  },
  sysLine: {
    width: 10,
    height: 2,
    borderRadius: 1,
  },
  setSlidersOutline: {
    width: 18,
    height: 18,
    borderRadius: 3,
    borderWidth: 1.8,
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  setDot1: {
    position: 'absolute',
    left: 3,
    top: 4,
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  setDot2: {
    position: 'absolute',
    right: 3,
    bottom: 4,
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
});
