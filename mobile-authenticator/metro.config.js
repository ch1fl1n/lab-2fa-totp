// La librería compartida totp-core vive fuera de este proyecto (../totp-core):
// Metro necesita vigilar esa carpeta para poder empaquetarla.
const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
config.watchFolders = [path.resolve(__dirname, '../totp-core')];

module.exports = config;
