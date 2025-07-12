import React from 'react';
import { View, StyleSheet, Dimensions, Text } from 'react-native';
import { useTheme } from '../context/ThemeContext';

const { width } = Dimensions.get('window');

interface AppHeaderProps {
  style?: any;
}

const AppHeader: React.FC<AppHeaderProps> = ({ style }) => {
  const { theme } = useTheme();

  return (
    <View style={[styles.headerContainer, style]}>
      <View style={styles.headerBrand}>
        <View style={styles.headerTextContainer}>
          <Text style={styles.headerTitle}>The Pulse Global</Text>
          <Text style={styles.headerSubtitle}>GEOPOLITICS</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  headerContainer: {
    width: '100%',
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 12,
    backgroundColor: '#000000',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  headerBrand: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTextContainer: {
    flexDirection: 'column',
    alignItems: 'center',
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  headerSubtitle: {
    color: '#cccccc',
    fontSize: 12,
    fontWeight: '400',
    marginTop: 2,
    letterSpacing: 1,
  },
});

export default AppHeader; 