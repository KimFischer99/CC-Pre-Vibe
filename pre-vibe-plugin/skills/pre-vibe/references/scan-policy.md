# Scan Policy

## Default Allowlist

- `README.md`, `README.*`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/rules/`
- `docs/`
- `package.json`, lockfiles, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`
- Source and test directory names as a tree summary only

## Default Denylist

- `.env`, `.env.*`
- private keys and certificates
- token caches
- local database dumps
- production logs
- credential files
- personal data exports

If environment information is needed, read variable names only after user approval; never read secret values by default.
