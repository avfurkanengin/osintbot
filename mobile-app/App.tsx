import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider } from 'react-native-paper';
import { StatusBar, View } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import FlashMessage from 'react-native-flash-message';
import PushNotification from 'react-native-push-notification';

import ConfirmedScreen from './src/screens/ConfirmedScreen';
import RejectedScreen from './src/screens/RejectedScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { ApiProvider } from './src/context/ApiContext';
import { ThemeProvider, useTheme } from './src/context/ThemeContext';
import AppHeader from './src/components/AppHeader';
import LoginScreen from './src/screens/LoginScreen';
import AsyncStorage from '@react-native-async-storage/async-storage';

const Tab = createBottomTabNavigator();

const AuthenticatedApp: React.FC = () => {
  const { theme, isDark } = useTheme();
  
  return (
    <PaperProvider theme={theme}>
      <NavigationContainer>
        <StatusBar 
          barStyle="light-content"
          backgroundColor="#000000"
          translucent={false}
        />
        <View style={{ flex: 1 }}>
          <AppHeader />
          <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused, color, size }) => {
              let iconName = 'home';
              
              if (route.name === 'Confirmed') {
                iconName = 'check-circle';
              } else if (route.name === 'Rejected') {
                iconName = 'cancel';
              } else if (route.name === 'Analytics') {
                iconName = 'analytics';
              } else if (route.name === 'Settings') {
                iconName = 'settings';
              }
              
              return <Icon name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: '#2196F3',
            tabBarInactiveTintColor: '#cccccc',
            tabBarStyle: {
              backgroundColor: '#1e1e1e',
              borderTopWidth: 1,
              borderTopColor: '#333333',
              paddingBottom: 5,
              height: 60,
            },
            headerShown: false,
          })}
        >
          <Tab.Screen 
            name="Confirmed" 
            component={ConfirmedScreen}
            options={{
              tabBarLabel: 'Confirmed',
            }}
          />
          <Tab.Screen 
            name="Rejected" 
            component={RejectedScreen}
            options={{
              tabBarLabel: 'Rejected',
            }}
          />
          <Tab.Screen 
            name="Analytics" 
            component={AnalyticsScreen}
            options={{
              tabBarLabel: 'Analytics',
            }}
          />
          <Tab.Screen 
            name="Settings" 
            component={SettingsScreen}
            options={{
              tabBarLabel: 'Settings',
            }}
          />
        </Tab.Navigator>
        </View>
      </NavigationContainer>
      <FlashMessage position="top" />
    </PaperProvider>
  );
};

const AppWithAuth: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
    
    // Inactivity timer
    let inactivityTimer = setTimeout(() => {
      PushNotification.localNotification({
        title: 'Inactivity Alert',
        message: 'No activity detected in the last 2 hours. Check the app!',
      });
    }, 2 * 60 * 60 * 1000);  // 2 hours

    return () => clearTimeout(inactivityTimer);
  }, []);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      setIsAuthenticated(!!token);
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  if (isLoading) {
    return null; // Or a loading screen
  }

  if (!isAuthenticated) {
    return (
      <ThemeProvider>
        <PaperProvider>
          <ApiProvider>
            <LoginScreen navigation={{ navigate: handleLoginSuccess }} />
            <FlashMessage position="top" />
          </ApiProvider>
        </PaperProvider>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <ApiProvider>
        <AuthenticatedApp />
      </ApiProvider>
    </ThemeProvider>
  );
};

export default AppWithAuth; 