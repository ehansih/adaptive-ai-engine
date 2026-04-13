import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.ehansih.adaptiveai',
  appName: 'Adaptive AI Engine',
  webDir: 'dist',
  server: {
    // For development/testing: point to your local or deployed backend
    // Change this to your server IP when testing on a real device
    url: 'http://10.0.2.2:8000',   // Android emulator → host machine
    cleartext: true,               // allow HTTP in dev (use HTTPS in prod)
  },
  android: {
    buildOptions: {
      keystorePath: 'release.keystore',
      keystorePassword: process.env.KEYSTORE_PASSWORD || '',
      keystoreAlias: 'adaptive-ai',
      keystoreAliasPassword: process.env.KEYSTORE_ALIAS_PASSWORD || '',
      releaseType: 'APK',
    },
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1500,
      backgroundColor: '#030712',
      androidSplashResourceName: 'splash',
      showSpinner: false,
    },
  },
};

export default config;
