import React, { useState, useCallback } from 'react';
import { View, StyleSheet, StatusBar } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '../state/NavigationContext';
import { useAppTheme } from '../theme/ThemeContext';
import { MainNavigationScreen } from '../screens/MainNavigationScreen';
import { SystemStatusScreen } from '../screens/SystemStatusScreen';
import { SettingsScreen } from '../screens/SettingsScreen';
import { BottomNavBar } from '../components/BottomNavBar';
import { SplashScreen } from '../components/SplashScreen';

export const AppNavigator: React.FC = () => {
  const { state, setActiveTab } = useNavigation();
  const { isDark, theme } = useAppTheme();
  const [showSplash, setShowSplash] = useState(true);
  const insets = useSafeAreaInsets();

  const handleFinishSplash = useCallback(() => {
    setShowSplash(false);
  }, []);

  return (
    <View style={[styles.rootContainer, { backgroundColor: theme.colors.background }]}>
      <StatusBar
        barStyle={isDark ? 'light-content' : 'dark-content'}
        backgroundColor="transparent"
        translucent={true}
      />

      {showSplash ? (
        <SplashScreen onFinish={handleFinishSplash} />
      ) : (
        <View style={[styles.mainWrapper, { paddingTop: insets.top, backgroundColor: theme.colors.surfaceHeader }]}>
          {/* Main Active Screen */}
          <View style={[styles.screenContent, { backgroundColor: theme.colors.background }]}>
            {state.activeTab === 'NAVIGATE' && <MainNavigationScreen />}
            {state.activeTab === 'SYSTEM' && <SystemStatusScreen />}
            {state.activeTab === 'SETTINGS' && <SettingsScreen />}
          </View>

          {/* Bottom Navigation Bar */}
          <BottomNavBar
            activeTab={state.activeTab}
            onTabChange={setActiveTab}
            bottomInset={insets.bottom}
          />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  rootContainer: {
    flex: 1,
  },
  mainWrapper: {
    flex: 1,
  },
  screenContent: {
    flex: 1,
  },
});
