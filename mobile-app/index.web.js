import { AppRegistry } from 'react-native';
import App from './App';

// Register the app for web
AppRegistry.registerComponent('OSINTBotMobile', () => App);

// Run the app
AppRegistry.runApplication('OSINTBotMobile', {
  initialProps: {},
  rootTag: document.getElementById('root'),
}); 