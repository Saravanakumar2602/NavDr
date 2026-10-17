import React, { createContext, useContext, useState } from 'react';
import { useColorScheme } from 'react-native';
import { ThemeMode, getTheme, ThemeColors } from './theme';

interface ThemeContextType {
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  isDark: boolean;
  theme: {
    isDark: boolean;
    colors: ThemeColors;
    spacing: Record<string, number>;
    borderRadius: Record<string, number>;
    typography: {
      fontFamily: string;
      sizes: Record<string, number>;
    };
  };
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  // Default appearance is LIGHT per NavDR Phase 1 specification
  const [themeMode, setThemeModeState] = useState<ThemeMode>('light');

  // Resolved active dark mode status
  const isDark =
    themeMode === 'system' ? systemColorScheme === 'dark' : themeMode === 'dark';

  const activeTheme = getTheme(isDark);

  const setThemeMode = (mode: ThemeMode) => {
    setThemeModeState(mode);
  };

  return (
    <ThemeContext.Provider
      value={{
        themeMode,
        setThemeMode,
        isDark,
        theme: activeTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useAppTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useAppTheme must be used within a ThemeProvider');
  }
  return context;
};
