const { FlatCompat } = require('@eslint/eslintrc');
const js = require('@eslint/js');

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

const baseConfig = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
    jest: true,
  },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    tsconfigRootDir: __dirname,
    project: [
      './tsconfig.json',
      './mcp-servers/tsconfig.json',
      './core/contract_service/contracts-L1/contracts/tsconfig.json',
      './island-ai/tsconfig.json',
      './core/advisory-database/tsconfig.json',
      './unmanned-engineer-ceo/tsconfig.json',
    ],
  },
  plugins: ['@typescript-eslint', 'import', 'prettier'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier',
  ],
  settings: {
    import: {
      resolver: {
        typescript: {
          alwaysTryTypes: true,
          project: ['./tsconfig.json', './island-ai/tsconfig.json'],
          extensionAlias: {
            '.js': ['.ts', '.tsx', '.d.ts'],
            '.mjs': ['.mts', '.d.mts'],
            '.cjs': ['.cts', '.d.cts'],
          },
        },
      },
    },
  },
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      },
    ],
    '@typescript-eslint/no-unused-expressions': 'off',
    'no-unused-expressions': [
      'error',
      {
        allowShortCircuit: true,
        allowTernary: true,
        allowTaggedTemplates: true,
      },
    ],
    '@typescript-eslint/no-non-null-assertion': 'warn',
    '@typescript-eslint/prefer-nullish-coalescing': 'error',
    '@typescript-eslint/prefer-optional-chain': 'error',
    '@typescript-eslint/strict-boolean-expressions': 'warn',
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/await-thenable': 'error',
    '@typescript-eslint/no-misused-promises': 'error',
    '@typescript-eslint/naming-convention': [
      'error',
      {
        selector: 'default',
        format: ['camelCase'],
      },
      {
        selector: 'variable',
        format: ['camelCase', 'UPPER_CASE'],
      },
      {
        selector: 'parameter',
        format: ['camelCase'],
        leadingUnderscore: 'allow',
      },
      {
        selector: 'memberLike',
        modifiers: ['private'],
        format: ['camelCase'],
        leadingUnderscore: 'require',
      },
      {
        selector: 'typeLike',
        format: ['PascalCase'],
      },
      {
        selector: 'enumMember',
        format: ['UPPER_CASE'],
      },
      {
        selector: 'interface',
        format: ['PascalCase'],
        custom: {
          regex: '^I[A-Z]',
          match: false,
        },
      },
    ],
    'import/order': [
      'error',
      {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true,
        },
      },
    ],
    'import/no-unresolved': 'error',
    'import/no-cycle': 'error',
    'import/no-duplicates': 'error',
    'prefer-const': 'error',
    'no-console': 'warn',
    'no-debugger': 'error',
    'no-alert': 'error',
    'no-var': 'error',
    eqeqeq: ['error', 'always'],
    curly: ['error', 'all'],
    'max-lines': [
      'warn',
      {
        max: 500,
        skipBlankLines: true,
        skipComments: true,
      },
    ],
    complexity: ['warn', 15],
    'prettier/prettier': 'error',
  },
  overrides: [
    {
      files: ['**/*.test.ts', '**/*.spec.ts', '**/__tests__/**'],
      parserOptions: {
        project: null,
      },
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        '@typescript-eslint/no-non-null-assertion': 'off',
        '@typescript-eslint/prefer-nullish-coalescing': 'off',
        '@typescript-eslint/strict-boolean-expressions': 'off',
        '@typescript-eslint/no-floating-promises': 'off',
        '@typescript-eslint/no-misused-promises': 'off',
        'max-lines': 'off',
      },
    },
    {
      files: ['*.config.ts', '*.config.js'],
      rules: {
        '@typescript-eslint/no-var-requires': 'off',
        'import/no-default-export': 'off',
      },
    },
    {
      files: ['core/advisory-database/**/*.ts', 'core/contract_service/contracts-L1/contracts/src/**/*.ts'],
      rules: {
        '@typescript-eslint/naming-convention': [
          'error',
          {
            selector: 'default',
            format: ['camelCase'],
          },
          {
            selector: 'variable',
            format: ['camelCase', 'UPPER_CASE', 'PascalCase'],
          },
          {
            selector: 'parameter',
            format: ['camelCase'],
            leadingUnderscore: 'allow',
          },
          {
            selector: 'property',
            format: ['camelCase', 'snake_case', 'UPPER_CASE', 'PascalCase'],
            leadingUnderscore: 'allow',
          },
          {
            selector: 'objectLiteralProperty',
            format: null,
          },
          {
            selector: 'memberLike',
            modifiers: ['private'],
            format: ['camelCase'],
            leadingUnderscore: 'allowSingleOrDouble',
          },
          {
            selector: 'typeLike',
            format: ['PascalCase'],
          },
          {
            selector: 'enumMember',
            format: ['UPPER_CASE'],
          },
        ],
        '@typescript-eslint/strict-boolean-expressions': 'off',
        '@typescript-eslint/explicit-function-return-type': 'off',
        '@typescript-eslint/require-await': 'off',
        '@typescript-eslint/prefer-nullish-coalescing': 'off',
        '@typescript-eslint/no-non-null-assertion': 'off',
        '@typescript-eslint/no-unsafe-assignment': 'off',
        '@typescript-eslint/no-unsafe-argument': 'off',
        '@typescript-eslint/no-unsafe-member-access': 'off',
        '@typescript-eslint/no-unsafe-call': 'off',
        '@typescript-eslint/no-unsafe-return': 'off',
        '@typescript-eslint/no-floating-promises': 'off',
        '@typescript-eslint/no-misused-promises': 'off',
        'import/no-unresolved': 'off',
        'import/no-named-as-default': 'off',
        'no-console': 'off',
      },
    },
  ],
  ignorePatterns: ['node_modules/', 'dist/', 'build/', 'coverage/', '*.min.js', '*.d.ts', '**/70-architecture-skeletons/**', 'mcp-servers/**/*.js'],
};

module.exports = compat.config(baseConfig);
