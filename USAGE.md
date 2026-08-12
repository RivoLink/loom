# Loom Usage Guide

## 1. Install

```bash
git clone https://github.com/RivoLink/loom && cd loom

python -m venv .venv && source .venv/bin/activate

make install          # pip install -e ".[dev,api]"
make install-termux   # for Termux
```

Requires Python 3.10+. Termux has a documented workaround (see [`README.md`](README.md)).

## 2. Start the server

```bash
make serve            # uvicorn loom.api.main:app on :8000
```

One process. No separate daemon, no deploy step. Each job spawns a
fresh subprocess so a crash in lxml or cryptography can't bring the
API down.

## 3. Submit a job (3 calls)

```bash
# POST: submit
curl -sX POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"target_name":"demo_dom_pagination","params":{"page":1}}'

# GET status: pending → running → finished
curl -s http://localhost:8000/jobs/<job_id>

# GET result once finished
curl -s http://localhost:8000/jobs/<job_id>/result | python -m json.tool
```

Or run `make demo` which chains the three on the `demo_dom_pagination` target.

For any other target, `make scrape <target_name> [<params_json>]` does
the same submit/poll/fetch dance :

```bash
make scrape demo_dom_minimal
make scrape demo_dom_pagination '{"page":1}'
make scrape demo_json_api '{"post_id":42}'
```

Params default to `{}` if omitted. `make demo` is just a shorthand for
`make scrape demo_dom_pagination '{"page":1}'`.

## 4. Add a YAML target

Drop a file in `configs/<target_name>.yaml` :

```yaml
name: mon_site
url: "https://example.com/produit/{id}"   # {id} comes from POST params
type: dom

pagination:
  type: next_link
  selector: "a.next::attr(href)"
  max_pages: 5

extract:
  titre:
    selector: "h1.product-title"
    transform: strip
  prix:
    selector: ".price"
    transform: [strip, to_number]
  images:
    selector: "img.product::attr(src)"
    multiple: true
```

Available immediately, no restart needed for the resolver (the API
reads the YAML on each job submission) :

```bash
curl -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"target_name":"<target_name>","params":{"id":42}}'
```

For a JSON API target, use `type: json_api` and `path: "$.field"`
(JSONPath) instead of `selector:`.

## 5. Add a custom transform (small bit of logic)

For a one-off quirky transformation, write it in
`loom/transforms/builtins.py` (or a new module imported by
`loom/transforms/__init__.py`) :

```python
@register_transform("parse_eur_price")
def _parse_eur(v):
    return float(v.replace("€", "").replace(",", ".").strip())
```

Reference it from any YAML config :

```yaml
prix:
  selector: ".price"
  transform: "custom:parse_eur_price"   # "custom:" prefix is optional
```

## 6. Add a custom spider (complex cases)

When YAML isn't expressive enough (multi-step navigation, conditional
logic, JS rendering, login flows), write a real Scrapy spider :

```python
# loom/spiders/custom/my_spider.py
import scrapy
from loom.spiders.custom import register_custom_spider


class MySpider(scrapy.Spider):
    name = "my_spider"

    async def start(self):
        yield scrapy.Request("https://...", callback=self.parse)

    def parse(self, response):
        yield {"title": response.css("h1::text").get()}


register_custom_spider("my_target", MySpider)
```

Then in `loom/spiders/custom/__init__.py` add :

```python
from . import my_spider   # noqa: F401 (triggers registration)
```

The resolver picks the custom spider over YAML when
`target_name == "my_target"`.

## 7. Test in dev

```bash
pytest                            # unit + API tests
LOOM_RUN_NETWORK_TESTS=1 pytest   # also e2e real crawl
```

## REST endpoints cheat-sheet

| Endpoint                    | Response                      |
|-----------------------------|-------------------------------|
| `POST /jobs`                | 202 `{job_id, spider}` or 404 |
| `GET /jobs/{job_id}`        | 200 `{job_id, status}`        |
| `GET /jobs/{job_id}/result` | 200 `{job_id, items}` or 409  |
| `GET /docs`                 | Swagger UI (auto-generated)   |

Possible job statuses : `pending`, `running`, `finished`, `failed`, `unknown`.

- `pending`: queued, the worker hasn't picked it up yet.
- `running`: the subprocess is actively crawling.
- `finished`: done, result file written, `/result` returns 200.
- `failed`: the subprocess crashed or raised, see API logs.
- `unknown`: job_id never seen and no result on disk (typo or
  restart with in-flight job).

## Environment variables

| Variable           | Default          | Purpose                          |
|--------------------|------------------|----------------------------------|
| `LOOM_RESULTS_DIR` | `<repo>/results` | where job results land           |
| `LOOM_CONFIGS_DIR` | `<repo>/configs` | where YAML configs are read from |

Both are inherited by the crawl subprocesses, so setting them once
before `make serve` is enough.

## Decision guide: YAML vs. transform vs. custom spider

| Situation                                      | Approach                     |
|------------------------------------------------|------------------------------|
| Simple selector → value                        | Plain YAML                   |
| Standard pagination (next_link)                | Plain YAML                   |
| Basic value transform (strip, regex, cast)     | Plain YAML                   |
| One quirky transform, otherwise simple page    | YAML + named hook            |
| Conditional extraction ("if empty, use other") | Named hook, or custom spider |
| JS interaction (infinite scroll, "load more")  | Custom spider                |
| Multi-step (login, cart, etc.)                 | Custom spider                |
| Highly site-specific recurring pattern         | Custom spider                |

A target can start as YAML and move to a custom spider later. The
resolver simply prefers the custom spider once registered, no other
code change needed.
