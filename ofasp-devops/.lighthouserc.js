module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3016',
        'http://localhost:3016/dashboard',
        'http://localhost:3016/api/health'
      ],
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--no-sandbox --headless',
        // Emulate mobile device for mobile performance testing
        emulatedFormFactor: 'desktop',
        // Network throttling
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
        },
        // Skip certain audits that might not be relevant
        skipAudits: [
          'uses-http2',
          'canonical'
        ]
      }
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.8 }],
        'categories:accessibility': ['warn', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['warn', { minScore: 0.8 }],
        'categories:pwa': 'off', // PWA not required for this project
        
        // Performance assertions
        'first-contentful-paint': ['warn', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        
        // Resource assertions
        'unused-javascript': ['warn', { maxLength: 3 }],
        'unused-css-rules': ['warn', { maxLength: 3 }],
        'unminified-css': 'error',
        'unminified-javascript': 'error',
        
        // Network assertions
        'uses-text-compression': 'error',
        'uses-responsive-images': 'warn',
        'efficient-animated-content': 'warn',
        
        // Accessibility assertions
        'color-contrast': 'error',
        'image-alt': 'error',
        'label': 'error',
        'valid-lang': 'error'
      }
    },
    upload: {
      target: 'temporary-public-storage',
      // In production, you might want to use:
      // target: 'lhci',
      // serverBaseUrl: 'https://your-lhci-server.com',
      // token: process.env.LIGHTHOUSE_CI_TOKEN
    },
    server: {
      // Configuration for LHCI server if used
    },
    wizard: {
      // Configuration for setup wizard
    }
  }
};