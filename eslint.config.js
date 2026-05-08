const eslint = require('@eslint/js');
const tseslint = require('typescript-eslint');
const vuePlugin = require('eslint-plugin-vue');
const prettierConfig = require('eslint-config-prettier');
const globals = require('globals');

module.exports = [
	eslint.configs.recommended,
	...tseslint.configs.recommended,
	...vuePlugin.configs['flat/recommended'],
	prettierConfig,
	{
		languageOptions: {
			globals: {
				...globals.browser,
				...globals.node,
				core: 'readonly',
				scripts: 'readonly'
			},
			parserOptions: {
				ecmaVersion: 'latest',
				sourceType: 'module'
			}
		},
		rules: {
			'max-len': ['error', { code: 120, tabWidth: 2, ignoreComments: true, ignoreStrings: true }],
			indent: 'off',
			camelcase: 'off',
			'vue/multi-word-component-names': 'off',
			'@typescript-eslint/no-explicit-any': 'off',
			'no-redeclare': 'off',
			'no-undef': 'off',
			'@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
			'@typescript-eslint/ban-ts-comment': 'warn',
			'@typescript-eslint/no-require-imports': 'off',
			'@typescript-eslint/no-unsafe-function-type': 'off',
			'@typescript-eslint/no-unused-expressions': 'off',
			'@typescript-eslint/triple-slash-reference': 'off'
		}
	},
	{
		ignores: ['**/dist/**', '**/lib/**', '**/node_modules/**', 'scripts/**', '*.js', 'packages/scripts/entry*.js']
	}
];
