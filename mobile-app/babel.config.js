module.exports = {
  presets: [
    ['@babel/preset-env', {
      targets: {
        web: true
      }
    }],
    '@babel/preset-react',
    '@babel/preset-typescript'
  ],
  plugins: [
    ['react-native-paper/babel'],
  ],
}; 