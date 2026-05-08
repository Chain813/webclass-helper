const { series } = require('gulp');
const { execOut } = require('./utils');

exports.default = series(() => execOut('tsc', { cwd: '../packages/core' }));
