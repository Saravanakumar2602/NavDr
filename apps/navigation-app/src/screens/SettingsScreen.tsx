import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Modal } from 'react-native';
import { useAppTheme } from '../theme/ThemeContext';
import { ThemeMode } from '../theme/theme';

export const SettingsScreen: React.FC = () => {
  const { themeMode, setThemeMode, theme } = useAppTheme();
  const [showAppearanceModal, setShowAppearanceModal] = useState(false);

  const getAppearanceLabel = () => {
    switch (themeMode) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      case 'system':
      default:
        return 'System Default';
    }
  };

  const handleSelectMode = (mode: ThemeMode) => {
    setThemeMode(mode);
    setShowAppearanceModal(false);
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]} contentContainerStyle={styles.content}>
      {/* Title */}
      <View style={styles.titleSection}>
        <Text style={[styles.sectionHeader, { color: theme.colors.primary }]}>PREFERENCES & CONFIGURATION</Text>
        <Text style={[styles.pageTitle, { color: theme.colors.textPrimary }]}>Settings</Text>
      </View>

      {/* APPEARANCE SECTION */}
      <View style={[styles.groupCard, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
        <Text style={[styles.groupTitle, { color: theme.colors.textSecondary }]}>APPEARANCE</Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <TouchableOpacity style={styles.row} onPress={() => setShowAppearanceModal(true)} activeOpacity={0.7}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Appearance</Text>
          <View style={styles.valChevronRow}>
            <Text style={[styles.rowValActive, { color: theme.colors.primary }]}>{getAppearanceLabel()}</Text>
            <Text style={[styles.rowChevron, { color: theme.colors.textMuted }]}> ›</Text>
          </View>
        </TouchableOpacity>
      </View>

      {/* NAVIGATION SECTION */}
      <View style={[styles.groupCard, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
        <Text style={[styles.groupTitle, { color: theme.colors.textSecondary }]}>NAVIGATION</Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Speed Units</Text>
          <Text style={[styles.rowVal, { color: theme.colors.textSecondary }]}>km/h</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Auto Recenter</Text>
          <Text style={[styles.rowValActive, { color: theme.colors.primary }]}>On</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Route Display</Text>
          <Text style={[styles.rowVal, { color: theme.colors.textSecondary }]}>GNSS + DR</Text>
        </View>
      </View>

      {/* SENSORS SECTION */}
      <View style={[styles.groupCard, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
        <Text style={[styles.groupTitle, { color: theme.colors.textSecondary }]}>SENSORS</Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>IMU Source</Text>
          <Text style={[styles.rowVal, { color: theme.colors.textSecondary }]}>Internal MEMS</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>External IMU</Text>
          <Text style={[styles.rowValMuted, { color: theme.colors.textMuted }]}>Off</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Sampling Rate</Text>
          <Text style={[styles.rowValActive, { color: theme.colors.primary }]}>200 Hz</Text>
        </View>
      </View>

      {/* MAP & DATA SECTION */}
      <View style={[styles.groupCard, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
        <Text style={[styles.groupTitle, { color: theme.colors.textSecondary }]}>MAP & DATA</Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Map Engine</Text>
          <Text style={[styles.rowValActive, { color: theme.colors.primary }]}>MapLibre</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Map Data</Text>
          <Text style={[styles.rowVal, { color: theme.colors.textSecondary }]}>OpenStreetMap Vector</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Offline Maps</Text>
          <Text style={[styles.rowValMuted, { color: theme.colors.textMuted }]}>Not configured</Text>
        </View>
      </View>

      {/* ABOUT SECTION */}
      <View style={[styles.groupCard, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
        <Text style={[styles.groupTitle, { color: theme.colors.textSecondary }]}>ABOUT</Text>
        <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>Diagnostics</Text>
          <Text style={[styles.rowChevron, { color: theme.colors.textMuted }]}>›</Text>
        </View>

        <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.textPrimary }]}>About NavDR</Text>
          <Text style={[styles.rowValActive, { color: theme.colors.primary }]}>v2.0 SIH 2026</Text>
        </View>
      </View>

      {/* APPEARANCE SELECTION MODAL */}
      <Modal
        visible={showAppearanceModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowAppearanceModal(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowAppearanceModal(false)}
        >
          <View style={[styles.modalBox, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
            <Text style={[styles.modalTitle, { color: theme.colors.textPrimary }]}>Select Appearance</Text>
            <View style={[styles.ruleDivider, { backgroundColor: theme.colors.cardBorder }]} />

            {/* System Default */}
            <TouchableOpacity
              style={styles.optionRow}
              onPress={() => handleSelectMode('system')}
              activeOpacity={0.7}
            >
              <View
                style={[
                  styles.radioCircle,
                  { borderColor: themeMode === 'system' ? theme.colors.primary : theme.colors.textMuted },
                ]}
              >
                {themeMode === 'system' && <View style={[styles.radioDot, { backgroundColor: theme.colors.primary }]} />}
              </View>
              <Text style={[styles.optionText, { color: theme.colors.textPrimary }]}>System Default</Text>
            </TouchableOpacity>

            <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

            {/* Light Mode */}
            <TouchableOpacity
              style={styles.optionRow}
              onPress={() => handleSelectMode('light')}
              activeOpacity={0.7}
            >
              <View
                style={[
                  styles.radioCircle,
                  { borderColor: themeMode === 'light' ? theme.colors.primary : theme.colors.textMuted },
                ]}
              >
                {themeMode === 'light' && <View style={[styles.radioDot, { backgroundColor: theme.colors.primary }]} />}
              </View>
              <Text style={[styles.optionText, { color: theme.colors.textPrimary }]}>Light</Text>
            </TouchableOpacity>

            <View style={[styles.rowDivider, { backgroundColor: theme.colors.cardBorder }]} />

            {/* Dark Mode */}
            <TouchableOpacity
              style={styles.optionRow}
              onPress={() => handleSelectMode('dark')}
              activeOpacity={0.7}
            >
              <View
                style={[
                  styles.radioCircle,
                  { borderColor: themeMode === 'dark' ? theme.colors.primary : theme.colors.textMuted },
                ]}
              >
                {themeMode === 'dark' && <View style={[styles.radioDot, { backgroundColor: theme.colors.primary }]} />}
              </View>
              <Text style={[styles.optionText, { color: theme.colors.textPrimary }]}>Dark</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 28,
  },
  titleSection: {
    marginBottom: 16,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  pageTitle: {
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  groupCard: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 14,
    marginBottom: 14,
  },
  groupTitle: {
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  ruleDivider: {
    height: 1,
    marginTop: 8,
    marginBottom: 10,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  valChevronRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rowLabel: {
    fontSize: 13,
    fontWeight: '700',
  },
  rowVal: {
    fontSize: 12,
    fontWeight: '700',
  },
  rowValActive: {
    fontSize: 12,
    fontWeight: '800',
  },
  rowValMuted: {
    fontSize: 12,
    fontWeight: '700',
  },
  rowChevron: {
    fontSize: 16,
    fontWeight: '600',
  },
  rowDivider: {
    height: 1,
    marginVertical: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalBox: {
    width: '100%',
    maxWidth: 320,
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  radioCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  radioDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  optionText: {
    fontSize: 14,
    fontWeight: '700',
  },
});
