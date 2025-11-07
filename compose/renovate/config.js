module.exports = {
	gitAuthor: 'Renovate Bot <renovate-bot@example.com>', // set the email address to whatever email your gave this user in your gitea
	username: 'renovate-bot',
    token: process.env.GITHUB_PAT,
    repositories: ['matthewkdies/homeserver', 'matthewkdies/football-pool'],
	onboardingConfig: {
		$schema: 'https://docs.renovatebot.com/renovate-schema.json',
		extends: ['config:recommended'],
	},
	persistRepoData: true,
};
