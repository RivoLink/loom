# loom

A generic, configuration-driven scraping service. Targets are defined as YAML configs and executed through a **Scrapy + FastAPI** stack.

## Layout

```bash
loom/             # Python package (spiders, config, transforms, API)
configs/          # YAML targets
results/          # JSON output per job_id (gitignored)
Makefile          # local orchestration
```

## Install

Requires **Python 3.10+** (the spider, config, and resolver modules use PEP 604 union syntax like `str | None`).

```bash
python -m venv .venv
source .venv/bin/activate

make install          # pip install -e ".[dev,api]"
make install-termux   # for Termux
```

### Termux (Android) native setup

Tested on Android 15 / kernel 6.6 / aarch64. Proot is not supported on this kernel (`execve` returns `ENOSYS`), but the full stack runs natively with the steps below.

```bash
# 1. Install heavy native dependencies via Termux prebuilts
pkg install python-cryptography python-lxml

# 2. Install Python dependencies
pip install --user scrapy pyyaml jsonpath-ng pytest pytest-asyncio \
                   pydantic fastapi 'uvicorn[standard]'

# 3. Pin cryptography to the Termux apt build.
#    The aarch64 wheel for cryptography 49.x currently ships a Rust
#    binding missing the PyExc_Warning symbol; fall back to the 48.x
#    build provided by apt.
pip uninstall -y cryptography
#    Repeat this step after any future `pip install` that upgrades
#    cryptography as a transitive dependency (scrapy, fastapi, etc.).

# 4. Install loom
pip install --user -e . --no-deps
```

Additional Termux-specific adjustments already built into the code:

- `LoomSpider` provides both entry points, `start_requests` (legacy) and `async start()` (Scrapy 2.13+), since Scrapy 2.16 requires the async generator entry point.
- `loom/config/schema.py` uses plain `dataclasses` instead of pydantic. This keeps the spider/config layer free of Rust dependencies; pydantic is only required by the FastAPI layer (`loom/api/`).

Verify the install:

```bash
pytest                            # unit + API tests
LOOM_RUN_NETWORK_TESTS=1 pytest   # also e2e real crawl
```

### Ruff on Termux

On Termux, `pip install ruff` triggers a Rust source build (no Termux-compatible
wheel is published on PyPI), which is slow. Install the prebuilt musl static
binary instead:

```bash
RUFF_VERSION=0.16.5
cd "$PREFIX/tmp"

curl -sL -o ruff.tar.gz \
  "https://github.com/astral-sh/ruff/releases/download/${RUFF_VERSION}/ruff-aarch64-unknown-linux-musl.tar.gz"

tar xzf ruff.tar.gz
install -m 755 ruff-aarch64-unknown-linux-musl/ruff ~/.local/bin/ruff

ruff --version
```

## Run the server

### Linux / macOS / Termux / WSL

```bash
make serve
```

Or without make:

```bash
export LOOM_RESULTS_DIR=$PWD/results
export LOOM_CONFIGS_DIR=$PWD/configs

mkdir -p "$LOOM_RESULTS_DIR"
uvicorn loom.api.main:app --port 8000
```

Stop with `Ctrl+C` (or `pkill -f "uvicorn loom"`).

### Windows native

The FastAPI server runs on Windows natively. Scrapyd, the previous blocker, is no longer a dependency.

```powershell
$env:LOOM_RESULTS_DIR = "$PWD\results"
$env:LOOM_CONFIGS_DIR = "$PWD\configs"

mkdir results -Force | Out-Null
uvicorn loom.api.main:app --port 8000
```

For dev iteration without the API, Scrapy's CLI is still available directly:

```powershell
scrapy crawl loom -a target_name=demo_dom_pagination -a params='{\"page\":1}'
scrapy crawl demo_custom_spider
```

Direct `scrapy crawl` writes to `results\<spider_name>.json` (no job_id). Use the API when you need job_ids and the full REST workflow.

## Usage examples (curl)

Once the API is running (`make serve`), the four shipped targets can be exercised as follows.
Replace `<job_id>` with the value returned by `POST /jobs`.

### Linux / macOS / Termux / WSL (bash)

```bash
# A. DOM + pagination on quotes.toscrape.com, max 3 pages
curl -s -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"target_name":"demo_dom_pagination","params":{"page":1}}'
# out: {"job_id":"...","spider":"loom"}

# B. JSON API, extracts post 42 via JSONPath
curl -s -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"target_name":"demo_json_api","params":{"post_id":42}}'

# C. Custom transform hook, author strings prefixed with CUR::
curl -s -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"target_name":"demo_dom_transform","params":{}}'

# D. Custom spider path, bypasses YAML, uses a hardcoded Python parser
curl -s -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"target_name":"demo_custom_spider","params":{}}'

# E. Unknown target, returns 404, no job is scheduled
curl -i -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"target_name":"does_not_exist","params":{}}'
# out: HTTP/1.1 404

# Poll status (repeat until "finished")
curl -s http://localhost:8000/jobs/<job_id>

# Fetch structured result
curl -s http://localhost:8000/jobs/<job_id>/result | python -m json.tool
```

For an arbitrary target without hand-writing the curl chain, use
`make scrape <target_name> [<params_json>]` :

```bash
make scrape demo_dom_minimal
make scrape demo_dom_pagination '{"page":1}'
make scrape demo_json_api '{"post_id":42}'
```

`make demo` is a shorthand for `make scrape demo_dom_pagination
'{"page":1}'`.

### Windows native (PowerShell)

Same payloads, with PowerShell-friendly quoting:

```powershell
# A. DOM + pagination
$res = Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs `
  -ContentType 'application/json' `
  -Body '{"target_name":"demo_dom_pagination","params":{"page":1}}'
$res            # out: job_id, spider

# B. JSON API
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs `
  -ContentType 'application/json' `
  -Body '{"target_name":"demo_json_api","params":{"post_id":42}}'

# C. Custom transform hook
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs `
  -ContentType 'application/json' `
  -Body '{"target_name":"demo_dom_transform","params":{}}'

# D. Custom spider
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs `
  -ContentType 'application/json' `
  -Body '{"target_name":"demo_custom_spider","params":{}}'

# E. Unknown target: Invoke-RestMethod throws on non-2xx; use
#    -SkipHttpErrorCheck (PowerShell 7+) or wrap in try/catch
try {
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs `
    -ContentType 'application/json' `
    -Body '{"target_name":"does_not_exist","params":{}}'
} catch { $_.Exception.Response.StatusCode.value__ }   # out: 404

# Poll status
Invoke-RestMethod -Uri "http://localhost:8000/jobs/$($res.job_id)"

# Fetch result
Invoke-RestMethod -Uri "http://localhost:8000/jobs/$($res.job_id)/result"
```

## Targets shipped

| target_name           | Type     | Spider               | Notes                                     |
|-----------------------|----------|----------------------|-------------------------------------------|
| `demo_dom_minimal`    | yaml/dom | `loom`               | example.com, minimal DOM extraction       |
| `demo_dom_pagination` | yaml/dom | `loom`               | quotes.toscrape.com, with pagination      |
| `demo_dom_transform`  | yaml/dom | `loom`               | demo `custom:fake_currency` hook          |
| `demo_json_api`       | yaml/api | `loom`               | jsonplaceholder.typicode.com, `{post_id}` |
| `demo_custom_spider`  | custom   | `demo_custom_spider` | demo custom-spider path                   |

## Adding a target

- **Plain YAML**: drop a file in `configs/{name}.yaml`. See `configs/demo_dom_minimal.yaml` as the simplest template, `configs/demo_dom_pagination.yaml` for a DOM example with pagination, or `configs/demo_json_api.yaml` for a JSON API example.
- **Custom spider**: write a `scrapy.Spider` subclass under `loom/spiders/custom/`, register it with `register_custom_spider("my_target", MySpider)`, and add the import in `loom/spiders/custom/__init__.py`.

## Adding a transform

```python
# loom/transforms/builtins.py
# or a new module imported by transforms/__init__.py
@register_transform("my_transform")
def _my(v): ...
```

Reference it from a config:

```yaml
extract:
  price:
    selector: ".price"
    transform: "custom:my_transform"     # "custom:" prefix is optional
```

## Environment variables

| Variable           | Default          | Used by                 |
|--------------------|------------------|-------------------------|
| `LOOM_RESULTS_DIR` | `<repo>/results` | pipeline + API          |
| `LOOM_CONFIGS_DIR` | `<repo>/configs` | config loader           |

Both variables are read by the FastAPI process and inherited by crawl subprocesses. The Makefile sets them automatically.

## Platform support

| Platform                       | Status                             |
|--------------------------------|------------------------------------|
| Linux (x86_64 / aarch64)       | Supported                          |
| macOS (Intel / Apple Silicon)  | Supported                          |
| Windows native                 | Supported                          |
| Windows + WSL                  | Supported (treat as Linux)         |
| Termux (Android)               | Supported (native, see above)      |

## Roadmap / current limitations

- No JS rendering, anti-bot handling, proxy rotation, or CAPTCHA solving.
- Authentication is limited to static headers.
- No config persistence in a database or result storage in S3.
- JSON API pagination is not yet wired (only DOM `next_link` is supported).
- The following endpoints are not yet implemented: synchronous `/scrape`, `POST /configs`, `DELETE /jobs/{id}`.
