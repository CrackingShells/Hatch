# Hatch

![Hatch Logo](./docs/resources/images/Logo/hatch_wide_dark_bg_transparent.png)

Hatch is the package manager for the Cracking Shells ecosystem. The documentation in `docs/index.md` is the canonical, up-to-date entry point for users and contributors — this README is a short pointer to those resources.

## Quick links

The major documentation entry points are:

- Documentation (canonical): `docs/index.md`
- Getting started (users): `docs/articles/users/GettingStarted.md`
- CLI reference: `docs/articles/users/CLIReference.md`
- Developer docs and architecture: `docs/articles/devs/index.md`

But, really, just look at the site: <https://crackingshells.github.io/Hatch/>

## Quick start

### Install from source

```bash
git clone https://github.com/CrackingShells/Hatch.git
cd Hatch
pip install -e .
```

Verify installation:

```bash
hatch --version
```

### Create a package template

```bash
hatch create my_package --description "My MCP server package"
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Quick Start

1. **Fork and clone** the repository
2. **Install dependencies**: `pip install -e .` and `npm install`
3. **Create a feature branch**: `git checkout -b feat/your-feature`
4. **Make changes** and add tests
5. **Use conventional commits**: `npm run commit` for guided commits
6. **Run tests**: `python -c "import hatch; print('Hatch package imports successfully')"`
7. **Create a pull request**

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning:

```bash
feat: add new feature
fix: resolve bug
docs: update documentation
test: add tests
chore: maintenance tasks
```

Use `npm run commit` for guided commit messages.

For detailed guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Getting Help

- Read developer onboarding and contribution guides in `docs/articles/devs/`
- Report issues or feature requests on the GitHub repository: <https://github.com/CrackingShells/Hatch/issues>

## License

This project is licensed under the GNU Affero General Public License v3 — see `LICENSE` for details.
