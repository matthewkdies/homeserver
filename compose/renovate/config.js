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
  extends: ['config:recommended', 'docker:pinDigests'],
  pinDigests: true,
  'docker-compose': {
    managerFilePatterns: [
      '/(^|/)[^/]+-compose\\.ya?ml$/',
      '/(^|/)(?:docker-)?compose[^/]*\\.ya?ml$/',
    ],
  },
  packageRules: [
    {
      description: 'Calendar Versioning for Pi-hole and Home Assistant',
      matchDatasources: ['docker'],
      matchPackageNames: [
        'pihole/pihole',
        'homeassistant/home-assistant',
        'ghcr.io/home-assistant/home-assistant',
      ],
      versioning:
        'regex:^(?<major>\\d{4})\\.(?<minor>\\d{1,2})\\.(?<patch>\\d+)(?:-(?<compatibility>.+))?$',
      separateMajorMinor: false,
    },
  ],
  persistRepoData: true,
  cacheDir: '/tmp/renovate/cache',
};
