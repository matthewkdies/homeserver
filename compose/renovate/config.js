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
  dockerMaxPages: 1000,
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
    {
      description: 'Keep MySQL on LTS release track',
      matchDatasources: ['docker'],
      matchPackageNames: ['mysql'],
      allowedVersions: '<9.0.0',
    },
    {
      description: 'Custom versioning for LinuxServer.io containers',
      matchDatasources: ['docker'],
      matchPackageNames: [
        '/^linuxserver\\/.+/',
        '/^lscr\\.io\\/linuxserver\\/.+/',
        '/^ghcr\\.io\\/linuxserver\\/.+/',
      ],
      versioning:
        'regex:^v?(?<major>\\d+)\\.(?<minor>\\d+)\\.(?<patch>\\d+)(?:[._-](?<build>[a-zA-Z0-9._-]+))?-ls(?<revision>\\d+)$',
    },
  ],
  persistRepoData: true,
  cacheDir: '/tmp/renovate/cache',
};
