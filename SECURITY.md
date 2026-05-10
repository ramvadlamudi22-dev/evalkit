# Security policy

## Supported versions

EvalKit follows semantic versioning. Until `v1.0.0` ships, only the latest tagged
release is supported. After `v1.0.0`, only the latest minor release line receives
security fixes.

| Version       | Supported |
|---------------|-----------|
| `0.x` (latest)| Yes       |
| `0.x` (older) | No        |

## Reporting a vulnerability

Please **do not** open public issues for security concerns. Instead:

1. Open a private security advisory:
   https://github.com/ramvadlamudi22-dev/evalkit/security/advisories/new

2. Or, if you cannot use GitHub Security Advisories, contact the maintainer
   directly via the email listed on the GitHub profile.

## Response targets

- **Acknowledgement**: within 7 days of receipt.
- **Mitigation or fix**: within 30 days of acknowledgement, or a written status
  update if more time is required.

## Scope

In scope:

- Code in this repository.
- The published Python package (`pip install evalkit`).
- The published container image (`ghcr.io/ramvadlamudi22-dev/evalkit`).

Out of scope:

- Third-party LLM provider behavior.
- Vulnerabilities in transitive dependencies that have no known impact on EvalKit
  (we still triage these via Dependabot, but they are not security advisories
  against EvalKit itself).
