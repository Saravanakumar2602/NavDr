import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { NavigationInstruction, ManeuverType } from '../../types/navigation';
import { useAppTheme } from '../../theme/ThemeContext';

interface NavigationHudCardProps {
  instruction: NavigationInstruction;
  distanceToDestinationMeters?: number;
  onEndNavigation: () => void;
}

export const NavigationHudCard: React.FC<NavigationHudCardProps> = ({
  instruction,
  distanceToDestinationMeters,
  onEndNavigation,
}) => {
  const { theme, isDark } = useAppTheme();

  const getManeuverIcon = (type: ManeuverType): string => {
    switch (type) {
      case 'TURN_RIGHT':
        return '↱';
      case 'SLIGHT_RIGHT':
        return '↗';
      case 'TURN_LEFT':
        return '↰';
      case 'SLIGHT_LEFT':
        return '↖';
      case 'U_TURN':
        return '↶';
      case 'ARRIVE':
        return '🏁';
      case 'CONTINUE':
      default:
        return '⬆';
    }
  };

  const formattedDistance =
    instruction.distanceMeters >= 1000
      ? `${(instruction.distanceMeters / 1000).toFixed(1)} km`
      : `${Math.round(instruction.distanceMeters / 10) * 10} m`;

  const formattedDestDist =
    distanceToDestinationMeters !== undefined && distanceToDestinationMeters > 0
      ? distanceToDestinationMeters >= 1000
        ? `${(distanceToDestinationMeters / 1000).toFixed(1)} km`
        : `${Math.round(distanceToDestinationMeters)} m`
      : null;

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: isDark ? '#1E293B' : '#0F172A', // Dark Slate Header
          borderColor: isDark ? '#334155' : '#1E293B',
        },
      ]}
    >
      <View style={styles.topRow}>
        <View style={styles.iconBox}>
          <Text style={styles.maneuverIcon}>{getManeuverIcon(instruction.type)}</Text>
        </View>

        <View style={styles.textContainer}>
          <Text style={styles.instructionTitle} numberOfLines={1}>
            {instruction.type === 'ARRIVE'
              ? 'ARRIVED AT DESTINATION'
              : instruction.type.replace('_', ' ')}
          </Text>

          {instruction.type !== 'ARRIVE' ? (
            <Text style={styles.distanceText}>
              in <Text style={styles.distanceHighlight}>{formattedDistance}</Text>
            </Text>
          ) : null}

          {instruction.roadName ? (
            <Text style={styles.roadNameText} numberOfLines={1}>
              onto {instruction.roadName}
            </Text>
          ) : null}
        </View>

        <TouchableOpacity
          onPress={onEndNavigation}
          style={styles.endBtn}
          activeOpacity={0.8}
          accessibilityLabel="End navigation"
          accessibilityRole="button"
        >
          <Text style={styles.endBtnText}>END</Text>
        </TouchableOpacity>
      </View>

      {formattedDestDist ? (
        <View style={styles.bottomRow}>
          <Text style={styles.destDistText}>
            Remaining to destination: <Text style={styles.destDistHighlight}>{formattedDestDist}</Text>
          </Text>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 14,
    elevation: 10,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#3B82F6', // Vivid Blue Accent
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  maneuverIcon: {
    fontSize: 22,
    color: '#FFFFFF',
    fontWeight: '900',
  },
  textContainer: {
    flex: 1,
    marginRight: 8,
  },
  instructionTitle: {
    fontSize: 16,
    fontWeight: '900',
    color: '#FFFFFF',
    letterSpacing: 0.6,
    marginBottom: 2,
  },
  distanceText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#94A3B8',
  },
  distanceHighlight: {
    color: '#38BDF8',
    fontWeight: '800',
  },
  roadNameText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#CBD5E1',
    marginTop: 2,
  },
  endBtn: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderWidth: 1,
    borderColor: '#EF4444',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  endBtnText: {
    color: '#EF4444',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.6,
  },
  bottomRow: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  destDistText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#94A3B8',
  },
  destDistHighlight: {
    color: '#F8FAFC',
    fontWeight: '800',
  },
});
