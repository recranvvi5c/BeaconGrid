# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.0.x | Yes |
| < 1.0 | No |

## Reporting a vulnerability

Please report security issues privately. Do **not** open a public issue for a
suspected vulnerability.

- Use GitHub's private vulnerability reporting ("Report a vulnerability" under the
  repository's Security tab), or
- Email the maintainers at `security@beacongrid.dev`.

Include a description of the issue, the affected runtime (Python or Go) and
version, reproduction steps or a proof of concept, and the impact you foresee.

## What to expect

- Acknowledgement of your report within 3 business days.
- An initial assessment and severity classification within 10 business days.
- Coordinated disclosure once a fix is available; we will credit reporters who
  wish to be named.

## Scope and hardening notes

BeaconGrid processes JSON records. The loader is the single entry point for
untrusted input and validates the schema discriminator before mapping fields.
When handling untrusted sessions or policies:

- Treat input files as untrusted data and run replays with least privilege.
- The tool performs no network or filesystem writes during a replay beyond
  emitting its report to stdout.
- Report any input that causes a crash, an unbounded resource use, or a bypass of
  the schema check as a security issue.

## Out of scope

- Vulnerabilities in third-party tooling used only for development.
- Issues requiring a modified build of BeaconGrid itself.
