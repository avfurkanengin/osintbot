import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Alert,
  Linking,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  TextInput,
  Switch,
  List,
  Divider,
  Dialog,
  Portal,
  Chip,
  SegmentedButtons,
} from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';
import { useApi } from '../context/ApiContext';
import { theme, spacing, borderRadius, shadows } from '../theme';

const SettingsScreen: React.FC = () => {
  const { state, setApiUrl } = useApi();
  const [apiUrlInput, setApiUrlInput] = useState(state.apiUrl);
  const [showApiDialog, setShowApiDialog] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [appVersion, setAppVersion] = useState('1.0.0');
  const [theme, setTheme] = useState<'light' | 'dark' | 'auto'>('auto');
  const [refreshInterval, setRefreshInterval] = useState('30');
  const [qualityThreshold, setQualityThreshold] = useState('0.6');
  const [showAdvanced, setShowAdvanced] = useState(false);

  React.useEffect(() => {
    loadSettings();
    getAppVersion();
  }, []);

  const loadSettings = async () => {
    try {
      const settings = await AsyncStorage.multiGet([
        'notifications',
        'autoRefresh',
        'theme',
        'refreshInterval',
        'qualityThreshold',
      ]);
      
      settings.forEach(([key, value]) => {
        if (value !== null) {
          switch (key) {
            case 'notifications':
              setNotifications(JSON.parse(value));
              break;
            case 'autoRefresh':
              setAutoRefresh(JSON.parse(value));
              break;
            case 'theme':
              setTheme(value as 'light' | 'dark' | 'auto');
              break;
            case 'refreshInterval':
              setRefreshInterval(value);
              break;
            case 'qualityThreshold':
              setQualityThreshold(value);
              break;
          }
        }
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const getAppVersion = async () => {
    try {
      const version = await DeviceInfo.getVersion();
      setAppVersion(version);
    } catch (error) {
      console.error('Failed to get app version:', error);
    }
  };

  const saveApiUrl = async () => {
    if (!apiUrlInput.trim()) {
      Alert.alert('Error', 'Please enter a valid API URL');
      return;
    }

    try {
      await setApiUrl(apiUrlInput.trim());
      setShowApiDialog(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to save API URL');
    }
  };

  const saveSetting = async (key: string, value: boolean | string) => {
    try {
      const valueToStore = typeof value === 'boolean' ? JSON.stringify(value) : value;
      await AsyncStorage.setItem(key, valueToStore);
    } catch (error) {
      console.error(`Failed to save ${key}:`, error);
    }
  };

  const handleNotificationToggle = (value: boolean) => {
    setNotifications(value);
    saveSetting('notifications', value);
  };

  const handleAutoRefreshToggle = (value: boolean) => {
    setAutoRefresh(value);
    saveSetting('autoRefresh', value);
  };

  const clearCache = async () => {
    Alert.alert(
      'Clear Cache',
      'This will clear all cached data. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.multiRemove(['posts', 'analytics', 'stats']);
              Alert.alert('Success', 'Cache cleared successfully');
            } catch (error) {
              Alert.alert('Error', 'Failed to clear cache');
            }
          },
        },
      ]
    );
  };

  const resetSettings = async () => {
    Alert.alert(
      'Reset Settings',
      'This will reset all settings to default. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.multiRemove([
                'apiUrl',
                'notifications',
                'autoRefresh',
              ]);
              setApiUrlInput('https://web-production-a5f83.up.railway.app');
              setNotifications(true);
              setAutoRefresh(true);
              Alert.alert('Success', 'Settings reset successfully');
            } catch (error) {
              Alert.alert('Error', 'Failed to reset settings');
            }
          },
        },
      ]
    );
  };

  const testConnection = async () => {
    try {
      const response = await fetch(`${state.apiUrl}/api/health`);
      if (response.ok) {
        Alert.alert('Success', 'Connection successful!');
      } else {
        Alert.alert('Error', 'Connection failed. Please check your API URL.');
      }
    } catch (error) {
      Alert.alert('Error', 'Connection failed. Please check your API URL and network connection.');
    }
  };

  return (
    <ScrollView style={styles.container}>
      {/* API Configuration */}
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.cardTitle}>API Configuration</Title>
          <List.Item
            title="API URL"
            description={state.apiUrl}
            left={(props) => <List.Icon {...props} icon="server" />}
            right={(props) => (
              <Button
                mode="outlined"
                onPress={() => setShowApiDialog(true)}
                compact
              >
                Edit
              </Button>
            )}
          />
          <Divider style={styles.divider} />
          <Button
            mode="outlined"
            onPress={testConnection}
            icon="wifi"
            style={styles.testButton}
          >
            Test Connection
          </Button>
        </Card.Content>
      </Card>

      {/* App Settings */}
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.cardTitle}>App Settings</Title>
          <List.Item
            title="Push Notifications"
            description="Receive notifications for new posts"
            left={(props) => <List.Icon {...props} icon="bell" />}
            right={() => (
              <Switch
                value={notifications}
                onValueChange={handleNotificationToggle}
                color={theme.colors.primary}
              />
            )}
          />
          <Divider style={styles.divider} />
          <List.Item
            title="Auto Refresh"
            description="Automatically refresh data every 30 seconds"
            left={(props) => <List.Icon {...props} icon="refresh" />}
            right={() => (
              <Switch
                value={autoRefresh}
                onValueChange={handleAutoRefreshToggle}
                color={theme.colors.primary}
              />
            )}
          />
        </Card.Content>
      </Card>

      {/* Appearance Settings */}
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.cardTitle}>Appearance</Title>
          <List.Item
            title="Theme"
            description="Choose app appearance"
            left={(props) => <List.Icon {...props} icon="palette" />}
          />
          <View style={styles.themeSelector}>
            <SegmentedButtons
              value={theme}
              onValueChange={(value) => {
                setTheme(value as 'light' | 'dark' | 'auto');
                saveSetting('theme', value);
              }}
              buttons={[
                { value: 'light', label: 'Light' },
                { value: 'dark', label: 'Dark' },
                { value: 'auto', label: 'Auto' },
              ]}
            />
          </View>
        </Card.Content>
      </Card>

      {/* Advanced Settings */}
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.cardTitle}>Advanced Settings</Title>
          <List.Item
            title="Show Advanced Options"
            description="Show additional configuration options"
            left={(props) => <List.Icon {...props} icon="settings" />}
            right={() => (
              <Switch
                value={showAdvanced}
                onValueChange={setShowAdvanced}
                color={theme.colors.primary}
              />
            )}
          />
          
          {showAdvanced && (
            <>
              <Divider style={styles.divider} />
              <List.Item
                title="Refresh Interval"
                description={`Refresh every ${refreshInterval} seconds`}
                left={(props) => <List.Icon {...props} icon="timer" />}
              />
              <View style={styles.intervalSelector}>
                <SegmentedButtons
                  value={refreshInterval}
                  onValueChange={(value) => {
                    setRefreshInterval(value);
                    saveSetting('refreshInterval', value);
                  }}
                  buttons={[
                    { value: '15', label: '15s' },
                    { value: '30', label: '30s' },
                    { value: '60', label: '1m' },
                    { value: '300', label: '5m' },
                  ]}
                />
              </View>
              
              <Divider style={styles.divider} />
              <List.Item
                title="Quality Threshold"
                description={`Minimum quality score: ${(parseFloat(qualityThreshold) * 100).toFixed(0)}%`}
                left={(props) => <List.Icon {...props} icon="star" />}
              />
              <View style={styles.qualitySelector}>
                <SegmentedButtons
                  value={qualityThreshold}
                  onValueChange={(value) => {
                    setQualityThreshold(value);
                    saveSetting('qualityThreshold', value);
                  }}
                  buttons={[
                    { value: '0.4', label: '40%' },
                    { value: '0.6', label: '60%' },
                    { value: '0.8', label: '80%' },
                  ]}
                />
              </View>
            </>
          )}
        </Card.Content>
      </Card>

      {/* Data Management */}
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.cardTitle}>Data Management</Title>
          <List.Item
            title="Clear Cache"
            description="Clear all cached data"
            left={(props) => <List.Icon {...props} icon="delete" />}
            right={() => (
              <Button
                mode="outlined"
                onPress={clearCache}
                textColor={theme.colors.error}
                compact
              >
                Clear
              </Button>
            )}
          />
          <Divider style={styles.divider} />
          <List.Item
            title="Reset Settings"
            description="Reset all settings to default"
            left={(props) => <List.Icon {...props} icon="restore" />}
            right={() => (
              <Button
                mode="outlined"
                onPress={resetSettings}
                textColor={theme.colors.error}
                compact
              >
                Reset
              </Button>
            )}
          />
        </Card.Content>
      </Card>

      {/* App Information */}
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.cardTitle}>App Information</Title>
          <List.Item
            title="Version"
            description={appVersion}
            left={(props) => <List.Icon {...props} icon="information" />}
          />
          <Divider style={styles.divider} />
          <List.Item
            title="Developer"
            description="OSINT Bot Mobile"
            left={(props) => <List.Icon {...props} icon="code-tags" />}
          />
          <Divider style={styles.divider} />
          <List.Item
            title="Support"
            description="Contact support for help"
            left={(props) => <List.Icon {...props} icon="help-circle" />}
            right={() => (
              <Button
                mode="outlined"
                onPress={() => Alert.alert('Support', 'Contact: support@osintbot.com')}
                compact
              >
                Contact
              </Button>
            )}
          />
        </Card.Content>
      </Card>

      {/* API URL Dialog */}
      <Portal>
        <Dialog
          visible={showApiDialog}
          onDismiss={() => setShowApiDialog(false)}
          style={styles.dialog}
        >
          <Dialog.Title>API Configuration</Dialog.Title>
          <Dialog.Content>
            <TextInput
              label="API URL"
              value={apiUrlInput}
              onChangeText={setApiUrlInput}
              placeholder="https://web-production-a5f83.up.railway.app"
              mode="outlined"
              style={styles.input}
            />
            <Paragraph style={styles.helpText}>
              Enter the URL of your OSINT Bot API server. Make sure it's accessible from your device.
            </Paragraph>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setShowApiDialog(false)}>Cancel</Button>
            <Button mode="contained" onPress={saveApiUrl}>
              Save
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  card: {
    margin: spacing.md,
    ...shadows.medium,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: spacing.sm,
  },
  divider: {
    marginVertical: spacing.sm,
  },
  testButton: {
    marginTop: spacing.sm,
  },
  dialog: {
    backgroundColor: theme.colors.surface,
  },
  input: {
    marginBottom: spacing.md,
  },
  helpText: {
    fontSize: 12,
    color: theme.colors.text,
    opacity: 0.7,
    lineHeight: 16,
  },
  themeSelector: {
    marginTop: spacing.sm,
    marginHorizontal: spacing.md,
  },
  intervalSelector: {
    marginTop: spacing.sm,
    marginHorizontal: spacing.md,
  },
  qualitySelector: {
    marginTop: spacing.sm,
    marginHorizontal: spacing.md,
  },
});

export default SettingsScreen; 