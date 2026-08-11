# Security Policy

## Supported Versions

Only the latest commit on the `main` branch is actively supported. Security fixes
are backported to the latest tagged release when one exists.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities privately through GitHub's Private Vulnerability Reporting:

<https://github.com/vishnuskandha/Behaviour.ai/security/advisories/new>

When reporting, please include:

- The affected component and commit/version
- A description of the vulnerability and its impact
- Steps to reproduce, if possible
- Any suggested remediation, if you have one

You should receive an acknowledgement within 5 business days, and a status update
(accepted, mitigated, or declined) once the report has been triaged.

## Security Notes

- The default `API_KEY` (`demo-secret-key`) is for local development only. Always
  set a strong key via the `API_KEY` environment variable in any real deployment.
- The dashboard embeds the demo key client-side for convenience; replace it with
  a server-side session/token mechanism for public deployments.
- The development server binds to `127.0.0.1` by default; reverse proxies and
  container deployments must bind deliberately (e.g. via Gunicorn config).
- Database credentials are read from environment variables (`DB_USER`,
  `DB_PASSWORD`) and must never be committed to the repository.
- The CI pipeline runs a static security scan (`bandit`) on every push and pull
  request; the configured severity threshold is defined in `.bandit`.
- Never commit secrets, API keys, private keys, or database dumps. The repo
  ships only example and demo values.
