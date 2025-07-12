import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Alert } from 'react-native';
import { Snackbar } from 'react-native-paper';

interface ErrorContextType {
  showError: (message: string, title?: string) => void;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
  clearError: () => void;
}

interface ErrorState {
  visible: boolean;
  message: string;
  type: 'error' | 'success' | 'warning' | 'info';
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

export const ErrorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [errorState, setErrorState] = useState<ErrorState>({
    visible: false,
    message: '',
    type: 'error',
  });

  const showMessage = (message: string, type: 'error' | 'success' | 'warning' | 'info') => {
    setErrorState({
      visible: true,
      message,
      type,
    });
  };

  const showError = (message: string, title?: string) => {
    if (title) {
      Alert.alert(title, message, [{ text: 'OK' }]);
    } else {
      showMessage(message, 'error');
    }
  };

  const showSuccess = (message: string) => {
    showMessage(message, 'success');
  };

  const showWarning = (message: string) => {
    showMessage(message, 'warning');
  };

  const showInfo = (message: string) => {
    showMessage(message, 'info');
  };

  const clearError = () => {
    setErrorState(prev => ({ ...prev, visible: false }));
  };

  const getSnackbarColor = () => {
    switch (errorState.type) {
      case 'error':
        return '#F44336';
      case 'success':
        return '#4CAF50';
      case 'warning':
        return '#FF9800';
      case 'info':
        return '#2196F3';
      default:
        return '#F44336';
    }
  };

  const value = {
    showError,
    showSuccess,
    showWarning,
    showInfo,
    clearError,
  };

  return (
    <ErrorContext.Provider value={value}>
      {children}
      <Snackbar
        visible={errorState.visible}
        onDismiss={clearError}
        duration={4000}
        style={{ backgroundColor: getSnackbarColor() }}
        action={{
          label: 'Dismiss',
          onPress: clearError,
        }}
      >
        {errorState.message}
      </Snackbar>
    </ErrorContext.Provider>
  );
}; 