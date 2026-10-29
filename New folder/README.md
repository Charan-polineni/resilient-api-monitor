# Resilient API Monitor

A practical Python service monitor that checks configured HTTP endpoints, handles common network failures, retries temporary errors with exponential backoff, stores every check in SQLite, and summarizes recent availability.

This is an intermediate project. It gives you real cases to work through: slow services, timeouts, flaky networks, bad configuration, repeated failures, and useful test coverage.

## What it does

- Checks multiple HTTP or HTTPS endpoints asynchronously
- Uses explicit timeouts and bounded retries with exponential backoff
- Treats HTTP 5xx and 429 responses as retryable; reports other HTTP responses accurately
- Stores check history in a local SQLite database
- Prints a readable status report and availability percentage
- Supports JSON configuration and command-line overrides
- Includes unit tests and a GitHub Actions workflow

## Requirements

- Python 3.11 or later
- No third-party Python packages are required
- Internet access to check real endpoints

## Run locally

```bash
git clone <your-repository-url>
cd resilient-api-monitor
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Run the example checks:

```bash
python -m api_monitor
```

Run with your own endpoints:

```bash
python -m api_monitor --url https://example.com --url https://www.python.org
```

Use a config file, shorter timeout, and custom database:

```bash
python -m api_monitor --config config.example.json --timeout 3 --db checks.sqlite3
```

Show recent history from the database:

```bash
python -m api_monitor --history 10
```

The program returns exit code `1` if any target is unhealthy, which makes it useful in scripts and scheduled jobs.

## Configuration

Copy `config.example.json` to `config.json` and edit the target list:

```json
{
  "targets": [
    {"name": "Example", "url": "https://example.com"},
    {"name": "Python", "url": "https://www.python.org"}
  ],
  "timeout_seconds": 5,
  "max_retries": 2,
  "backoff_seconds": 0.5
}
```

Configuration is validated before any network request is made. `config.json` is ignored by Git so you can keep your personal target list local.

## Project structure

```text
api_monitor/
  __init__.py
  __main__.py       CLI and exit status
  checker.py        Async HTTP checking and retry behavior
  config.py         Config loading and validation
  database.py       SQLite history storage and availability queries
  models.py         Typed data records
tests/
  test_checker.py
  test_config.py
  test_database.py
.github/workflows/tests.yml
config.example.json
pyproject.toml
```

## Tests

Run the test suite with Python's built-in unittest:

```bash
python -m unittest discover -s tests -v
```

Tests use a local fake HTTP server and temporary database files. They do not need public internet access.

## GitHub learning challenges

Try these one at a time, committing after each completed change:

1. Add a `--workers` option to limit how many checks run at the same time.
2. Add a `--format json` option for machine-readable reports.
3. Add a warning when response time exceeds a configurable threshold.
4. Write a test for malformed JSON and another for a URL without a scheme.
5. Create a branch for one feature, open a pull request, and merge it after CI passes.
6. Deliberately create a merge conflict in `README.md`, then resolve it and commit the result.

## Design notes

- Retry delays are bounded, preventing a bad endpoint from keeping the program busy indefinitely.
- Each check records attempts, status code when available, elapsed time, and an error description.
- SQLite writes are serialized after parallel checks complete, keeping the database access straightforward.
- This is a local monitor, not a production alerting service. It does not run continuously or send notifications.

## License

MIT. See [LICENSE](LICENSE).
