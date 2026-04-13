import type { CapacitorConfig } from '@capacitor/cli';

const isDev = process.env.NODE_ENV !== 'production';

const config: CapacitorConfig = {
  appId: 'com.ehansih.adaptiveai',
  appName: 'Adaptive AI Engine',
  webDir: 'dist',
  // No hardcoded server URL — app reads VITE_API_URL at build time
  // or falls back to the in-app settings screen for runtime configuration
  ...(isDev && {
    server: {
      url: 'http://10.0.2.2:8000',  // emulator only — dev builds
      cleartext: true,
    },
  }),
  android: {
    buildOptions: {
      keystorePath: process.env.KEYSTORE_PATH || 'release.keystore',
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
