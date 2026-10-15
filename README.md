### Realtime Marketplace

A custom Frappe marketplace with product browsing, buyer/seller orders, mobile
sessions, and user-scoped realtime order events.

Read [the architecture guide](docs/architecture.md) for the directory map,
dependency rules, stable API routes, realtime behavior, and where future code
belongs. The API delegates to focused services; Frappe DocType files keep their
required locations.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/idipangkar-ai/realtime-frappe-server.git --branch develop
bench --site your-site.local install-app realtime_marketplace
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/realtime_marketplace
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
