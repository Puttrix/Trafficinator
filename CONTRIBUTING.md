# Contributing to Trafficinator

Thanks for your interest in helping improve Trafficinator! Contributions are welcome and appreciated. This guide walks you through the process for reporting issues, proposing changes, and submitting pull requests.

## Getting Started

1. **Fork & clone** the repository.
2. **Install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r dev-requirements.txt
   ```
3. **Install frontend tooling** (optional, for UI work):
   ```bash
   npm install
   ```
4. **Run the test suite** to ensure everything passes before you begin:
   ```bash
   python3 -m pytest matomo-load-baked/tests
   ```

## Development Workflow

1. Create a feature branch off `develop`.
2. Make focused commits with clear messages.
3. Keep your branch rebased with the upstream `develop` branch.
4. Add or update tests and documentation when applicable.
5. Run the relevant test suites and linters before opening a pull request.

## Commit Messages

- Use the imperative mood (e.g., "Add loader retry logic").
- Reference GitHub issues when appropriate (`Fixes #123`).
- Group related changes within a single commit; avoid mixing unrelated work.

## Pull Requests

1. Push your branch to your fork.
2. Open a pull request against `develop`.
3. Fill out the PR template, summarizing the change, testing performed, and any follow-up work.
4. Be responsive to review feedback and keep the conversation respectful.

## Reporting Bugs

- Check existing issues to avoid duplicates.
- Include steps to reproduce, expected vs. actual behavior, logs, and screenshots where relevant.
- Provide environment details (OS, Python version, Docker version, etc.).

## Feature Requests

- Describe the problem the feature solves.
- Highlight any alternatives you considered.
- Share mockups or diagrams when useful.

## Security

For security vulnerabilities, please follow the process outlined in `SECURITY.md`. Do not open public issues for potential vulnerabilities.

## Recognition

Trafficinator follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold these standards. Thank you for helping make the project better!
