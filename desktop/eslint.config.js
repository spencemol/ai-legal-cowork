import js from '@eslint/js'
import tsPlugin from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import reactHooksPlugin from 'eslint-plugin-react-hooks'
import reactRefreshPlugin from 'eslint-plugin-react-refresh'

const browserGlobals = {
  window: 'readonly',
  document: 'readonly',
  console: 'readonly',
  fetch: 'readonly',
  Response: 'readonly',
  RequestInit: 'readonly',
  ReadableStream: 'readonly',
  TextDecoder: 'readonly',
  TextEncoder: 'readonly',
  AbortController: 'readonly',
  localStorage: 'readonly',
  HTMLElement: 'readonly',
  HTMLTextAreaElement: 'readonly',
  HTMLSpanElement: 'readonly',
  HTMLDivElement: 'readonly',
  JSX: 'readonly',
}

const nodeGlobals = {
  global: 'writable',
  process: 'readonly',
  __dirname: 'readonly',
  __filename: 'readonly',
  module: 'readonly',
  require: 'readonly',
}

export default [
  { ignores: ['dist', 'node_modules'] },
  js.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...browserGlobals,
        ...nodeGlobals,
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      'react-hooks': reactHooksPlugin,
      'react-refresh': reactRefreshPlugin,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'no-undef': 'off', // TypeScript handles this
    },
  },
]
