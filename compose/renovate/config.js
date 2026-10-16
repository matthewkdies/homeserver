const fs = require('fs');

let token = process.env.RENOVATE_TOKEN;
if (!token && process.env.RENOVATE_TOKEN_FILE && fs.existsSync(process.env.RENOVATE_TOKEN_FILE)) {
  token = fs.readFileSync(process.env.RENOVATE_TOKEN_FILE, 'utf8').trim();
}

module.exports = {
  platform: 'github',
  token: token,
  repositories: ['matthewkdies/homeserver'],
  gitAuthor: 'Renovate Bot <renovate@mattdies.com>',
  onboarding: false,
  requireConfig: 'optional',
  'docker-compose': {
    managerFilePatterns: [
      '/(^|/)[^/]+-compose\\.ya?ml$/',
      '/(^|/)(?:docker-)?compose[^/]*\\.ya?ml$/',
    ],
  },
  persistRepoData: true,
  cacheDir: '/tmp/renovate/cache',
};
