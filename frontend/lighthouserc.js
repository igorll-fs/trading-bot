module.exports = {
  ci: {
    collect: {
      url: [
        'http://127.0.0.1:3000/',
        'http://127.0.0.1:3000/settings',
        'http://127.0.0.1:3000/trades',
        'http://127.0.0.1:3000/instructions',
      ],
      numberOfRuns: 1,
      startServerCommand: 'yarn start:ci',
      startServerReadyPattern: 'Compiled successfully',
      startServerReadyTimeout: 120_000,
      settings: {
        preset: 'desktop',
        formFactor: 'desktop',
        screenEmulation: {
          disabled: true,
        },
      },
    },
    assert: {
      preset: 'lighthouse:recommended',
      assertions: {
        'categories:accessibility': ['warn', { minScore: 0.9 }],
        'categories:performance': ['warn', { minScore: 0.7 }],
      },
    },
    upload: {
      target: 'filesystem',
      outputDir: './lhci-report',
    },
  },
};
