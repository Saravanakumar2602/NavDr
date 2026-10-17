export type ThemeMode = 'system' | 'light' | 'dark';

export interface ThemeColors {
  background: string;
  surfaceHeader: string;
  card: string;
  cardHeader: string;
  cardBorder: string;
  cardBorderAccent: string;

  primary: string;
  accent: string;
  gnssHealthy: string;
  gnssDenied: string;
  gnssRecovering: string;

  gnssPath: string;
  idrPath: string;
  mapMatchedPath: string;
  lastKnownGnssPoint: string;

  textPrimary: string;
  textSecondary: string;
  textMuted: string;

  primaryButton: string;
  primaryButtonText: string;
  outageButton: string;
  outageButtonText: string;
  recoverButton: string;
  recoverButtonText: string;
  secondaryButton: string;
  secondaryButtonText: string;

  mapBackground: string;
  mapGrid: string;
  mapCompassRing: string;
  roadMajor: string;
  roadMinor: string;
  roadOutline: string;
  vehicleMarker: string;
  vehiclePulse: string;
  vehicleDrMarker: string;
  vehicleDrPulse: string;
  accuracyCircle: string;
  accuracyDrCircle: string;
}

export const lightColors: ThemeColors = {
  background: '#F8FAFC',
  surfaceHeader: '#FFFFFF',
  card: '#FFFFFF',
  cardHeader: '#F1F5F9',
  cardBorder: '#E2E8F0',
  cardBorderAccent: 'rgba(37, 99, 235, 0.3)',

  primary: '#2563EB',
  accent: '#2563EB',
  gnssHealthy: '#10B981',
  gnssDenied: '#EF4444',
  gnssRecovering: '#F59E0B',

  gnssPath: '#2563EB',
  idrPath: '#F97316',
  mapMatchedPath: '#10B981',
  lastKnownGnssPoint: '#EF4444',

  textPrimary: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#94A3B8',

  primaryButton: '#2563EB',
  primaryButtonText: '#FFFFFF',
  outageButton: 'rgba(239, 68, 68, 0.12)',
  outageButtonText: '#EF4444',
  recoverButton: 'rgba(16, 185, 129, 0.12)',
  recoverButtonText: '#10B981',
  secondaryButton: '#F1F5F9',
  secondaryButtonText: '#475569',

  mapBackground: '#F1F5F9',
  mapGrid: '#E2E8F0',
  mapCompassRing: '#CBD5E1',
  roadMajor: '#CBD5E1',
  roadMinor: '#E2E8F0',
  roadOutline: '#94A3B8',
  vehicleMarker: '#2563EB',
  vehiclePulse: 'rgba(37, 99, 235, 0.18)',
  vehicleDrMarker: '#F97316',
  vehicleDrPulse: 'rgba(249, 115, 22, 0.18)',
  accuracyCircle: 'rgba(37, 99, 235, 0.08)',
  accuracyDrCircle: 'rgba(249, 115, 22, 0.10)',
};

export const darkColors: ThemeColors = {
  background: '#090D16',
  surfaceHeader: '#0F172A',
  card: '#0F172A',
  cardHeader: '#1E293B',
  cardBorder: '#1E293B',
  cardBorderAccent: 'rgba(56, 189, 248, 0.3)',

  primary: '#38BDF8',
  accent: '#38BDF8',
  gnssHealthy: '#10B981',
  gnssDenied: '#EF4444',
  gnssRecovering: '#F59E0B',

  gnssPath: '#38BDF8',
  idrPath: '#F97316',
  mapMatchedPath: '#10B981',
  lastKnownGnssPoint: '#EF4444',

  textPrimary: '#F8FAFC',
  textSecondary: '#94A3B8',
  textMuted: '#64748B',

  primaryButton: '#38BDF8',
  primaryButtonText: '#090D16',
  outageButton: 'rgba(239, 68, 68, 0.15)',
  outageButtonText: '#EF4444',
  recoverButton: 'rgba(16, 185, 129, 0.15)',
  recoverButtonText: '#10B981',
  secondaryButton: '#1E293B',
  secondaryButtonText: '#94A3B8',

  mapBackground: '#0B1329',
  mapGrid: '#1E293B',
  mapCompassRing: '#334155',
  roadMajor: '#1E293B',
  roadMinor: '#131C31',
  roadOutline: '#0F172A',
  vehicleMarker: '#38BDF8',
  vehiclePulse: 'rgba(56, 189, 248, 0.20)',
  vehicleDrMarker: '#F97316',
  vehicleDrPulse: 'rgba(249, 115, 22, 0.20)',
  accuracyCircle: 'rgba(56, 189, 248, 0.08)',
  accuracyDrCircle: 'rgba(249, 115, 22, 0.10)',
};

export const getTheme = (isDark: boolean) => ({
  isDark,
  colors: isDark ? darkColors : lightColors,
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 18,
    xl: 24,
  },
  borderRadius: {
    xs: 4,
    sm: 6,
    md: 10,
    lg: 14,
    pill: 9999,
  },
  typography: {
    fontFamily: 'System',
    sizes: {
      xs: 10,
      sm: 12,
      md: 14,
      lg: 16,
      xl: 20,
      xxl: 26,
    },
  },
});

export const theme = getTheme(false);
