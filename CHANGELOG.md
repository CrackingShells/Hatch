## [1.0.0-dev.1](https://github.com/CrackingShells/Hatch/compare/v0.6.2...v1.0.0-dev.1) (2025-09-08)


### ⚠ BREAKING CHANGES

* Replace custom dual-file versioning system with semantic-release.
All future commits must follow Conventional Commits format.

- Remove custom versioning scripts (300+ lines eliminated)
- Remove VERSION and VERSION.meta files
- Remove custom GitHub Actions workflows
- Add semantic-release configuration and workflows
- Add commitizen for guided commit messages
- Add commitlint for PR validation
- Update pyproject.toml to static versioning
- Update documentation for new workflow

This migration eliminates complex custom code and adopts industry-standard
automated versioning practices consistent with the CrackingShells organization.

### ci

* migrate to semantic-release ([cec8e28](https://github.com/CrackingShells/Hatch/commit/cec8e28a781a0d4aad147ad607faf78985af230c))


### Documentation

* enable Python requirements installation for documentation build ([#35](https://github.com/CrackingShells/Hatch/issues/35)) ([ba03817](https://github.com/CrackingShells/Hatch/commit/ba038170a62e23c0575ae76194ab189222bc6e78))
* enhance documentation with API reference and mkdocstrings integration ([#34](https://github.com/CrackingShells/Hatch/issues/34)) ([34a8fa2](https://github.com/CrackingShells/Hatch/commit/34a8fa260f91570ae94192f1c6e4ab62d4a2c834))
* update documentation theme to Material and add mkdocs-material dependency ([#36](https://github.com/CrackingShells/Hatch/issues/36)) ([20825d8](https://github.com/CrackingShells/Hatch/commit/20825d81a8a7df0866f964d5dd4090b04305bb5a))
