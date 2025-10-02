# Support

Thanks for using BeaconGrid. Here is how to get help.

## Before you ask

- Read the [README](README.md) for an overview and quickstart.
- Follow the [usage guide](docs/USAGE.md) for the CLI and Python API.
- Check the [format reference](docs/FORMATS.md) if a session or policy fails to
  load — most load errors are schema or field issues.
- Run `validate` on your file to get a precise diagnosis:
  ```bash
  python -m beacongrid validate session path/to/session.json
  python -m beacongrid validate policy  path/to/policy.json
  ```

## Asking a question

Open a **Question** issue or start a discussion. Please include:

- What you ran (the exact command or code) and what you expected.
- The output you got, including any error message.
- Your runtime and version: `python --version` or `go version`.
- A minimal session/policy that reproduces the behavior, if possible.

## Reporting bugs and requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`. A minimal reproduction
makes bugs dramatically faster to fix.

## Security issues

Do not file security reports as public issues. Follow [SECURITY.md](SECURITY.md).

## Response expectations

BeaconGrid is maintained on a best-effort basis. We aim to triage new issues
within a few business days. Clear, reproducible reports are prioritized.
