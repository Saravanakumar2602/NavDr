import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { PlaceSearchResult } from '../../types/navigation';
import { useAppTheme } from '../../theme/ThemeContext';

interface SearchResultsListProps {
  results: PlaceSearchResult[];
  onSelectResult: (result: PlaceSearchResult) => void;
  isLoading?: boolean;
  error?: string;
  isOffline?: boolean;
  query: string;
}

export const SearchResultsList: React.FC<SearchResultsListProps> = ({
  results,
  onSelectResult,
  isLoading,
  error,
  isOffline,
  query,
}) => {
  const { theme } = useAppTheme();

  if (query.trim().length < 2) {
    return null;
  }

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.card,
          borderColor: theme.colors.cardBorder,
        },
      ]}
    >
      {isLoading ? (
        <View style={styles.messageBox}>
          <Text style={[styles.messageText, { color: theme.colors.textSecondary }]}>
            Searching places...
          </Text>
        </View>
      ) : isOffline || error ? (
        <View style={styles.messageBox}>
          <Text style={styles.errorIcon}>📡</Text>
          <Text style={[styles.errorTitle, { color: theme.colors.textPrimary }]}>
            {isOffline ? 'Search Unavailable Offline' : 'Search Error'}
          </Text>
          <Text style={[styles.errorSub, { color: theme.colors.textMuted }]}>
            {error || 'Unable to connect to geocoding service.'}
          </Text>
        </View>
      ) : results.length === 0 ? (
        <View style={styles.messageBox}>
          <Text style={styles.emptyIcon}>🔍</Text>
          <Text style={[styles.messageText, { color: theme.colors.textSecondary }]}>
            No destinations found for "{query}"
          </Text>
        </View>
      ) : (
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          keyboardShouldPersistTaps="handled"
          ItemSeparatorComponent={() => (
            <View style={[styles.separator, { backgroundColor: theme.colors.cardBorder }]} />
          )}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.itemContainer}
              onPress={() => onSelectResult(item)}
              activeOpacity={0.7}
            >
              <View style={[styles.iconBox, { backgroundColor: 'rgba(59, 130, 246, 0.12)' }]}>
                <Text style={styles.pinIcon}>📍</Text>
              </View>

              <View style={styles.itemTextContainer}>
                <Text
                  style={[styles.itemName, { color: theme.colors.textPrimary }]}
                  numberOfLines={1}
                >
                  {item.name}
                </Text>
                <Text
                  style={[styles.itemAddress, { color: theme.colors.textSecondary }]}
                  numberOfLines={2}
                >
                  {item.address}
                </Text>
              </View>

              {item.type ? (
                <View style={[styles.badge, { backgroundColor: theme.colors.background }]}>
                  <Text style={[styles.badgeText, { color: theme.colors.textMuted }]}>
                    {item.type}
                  </Text>
                </View>
              ) : null}
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    maxHeight: 280,
    borderRadius: 14,
    borderWidth: 1,
    marginTop: 8,
    overflow: 'hidden',
    elevation: 8,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
  },
  itemContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  iconBox: {
    width: 34,
    height: 34,
    borderRadius: 17,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  pinIcon: {
    fontSize: 16,
  },
  itemTextContainer: {
    flex: 1,
    marginRight: 8,
  },
  itemName: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  itemAddress: {
    fontSize: 12,
    fontWeight: '400',
    lineHeight: 16,
  },
  badge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  separator: {
    height: 1,
    marginLeft: 60,
  },
  messageBox: {
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyIcon: {
    fontSize: 24,
    marginBottom: 6,
  },
  errorIcon: {
    fontSize: 24,
    marginBottom: 6,
  },
  messageText: {
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
  errorTitle: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 4,
  },
  errorSub: {
    fontSize: 12,
    textAlign: 'center',
  },
});
