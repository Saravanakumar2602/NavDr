import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAppTheme } from '../theme/ThemeContext';

interface NarrationSubtitleCardProps {
  step: number;
}

const NARRATION_SCRIPTS: Record<number, string> = {
  1: 'Search destination → select target location',
  2: 'Offline route generated → route polyline calculated',
  3: 'Turn-by-turn instruction → HUD guidance active',
  4: 'GNSS available → 3D lock active, vehicle marker moving',
  5: 'GNSS DENIED → Dead Reckoning & AI motion estimation active',
  6: 'DR trajectory + map matching maintaining route alignment',
  7: 'GNSS returning → verifying satellite lock',
  8: 'GNSS RECOVERED → system restored to 3D GNSS lock',
};

export const NarrationSubtitleCard: React.FC<NarrationSubtitleCardProps> = () => {
  return null;
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 80,
    left: 14,
    right: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    zIndex: 40,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  badge: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
    lineHeight: 16,
  },
});
