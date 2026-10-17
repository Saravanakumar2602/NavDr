import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ThemeProvider } from './src/theme/ThemeContext';
import { NavigationProvider } from './src/state/NavigationContext';
import { AppNavigator } from './src/navigation/AppNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <NavigationProvider>
          <AppNavigator />
        </NavigationProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}


