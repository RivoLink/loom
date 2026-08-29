# Contributing

Thank you for your interest in contributing to `loom`.

## Getting Started

1. Fork the repository.
2. Clone your fork:

```bash
git clone https://github.com/<your-username>/loom.git
cd loom
```

3. Create a virtualenv (Python 3.10+ required):

```bash
python -m venv .venv && source .venv/bin/activate
```

4. Install the project and its locked dependencies:

```bash
make install            # standard Linux / macOS / WSL
make install-termux     # Termux (Android) native setup
```

5. Run the API:

```bash
make serve
```

6. Submit a demo job (in another shell, once the server is up):

```bash
make demo
```

## Development Workflow

Before submitting a PR, run the full validation sequence:

```bash
pytest                              # unit + integration (network tests skipped)
LOOM_RUN_NETWORK_TESTS=1 pytest     # full suite incl. real e2e crawls
```

If you touched dependency metadata in `pyproject.toml`, refresh the lock file:

```bash
make lock                           # regenerate requirements.lock
```

## Pull Requests

1. Create a feature branch from `main`.
2. Make focused changes.
3. Keep `README.md`, `USAGE.md` and the specs under `docs/` in sync when behavior changes.
4. Ensure all checks pass.
5. Open a PR with a clear description of:
   - what changed;
   - why it changed;
   - how it was tested.

## Commit Messages

- Use clear, direct messages.
- Keep the first line short.
- Prefer the existing prefixes used in the repository when they fit.

Examples:

- `feat: JSON API pagination`
- `chore: scheduler subprocess`
- `fix: JsonFilePipeline warning`
- `docs: make scrape guide`

## Code Style

- Follow the existing Python style in the repository (PEP 8, 4-space indent).
- Prefer `str | None` over `Optional[str]` (PEP 604, project baseline is 3.10+).
- Keep the `loom/config/` and `loom/spiders/` layers free of pydantic and other Rust-backed deps; pydantic stays confined to `loom/api/`.
- Prefer small, targeted refactors over broad rewrites.
- Keep ASCII by default unless the file already uses Unicode intentionally.

## Testing Notes

- Add regression tests when fixing a spider, config resolver or transform bug.
- Prefer narrow, behavior-focused tests over full end-to-end crawls when possible.
- Real network calls belong behind the `LOOM_RUN_NETWORK_TESTS=1` gate so the default `pytest` run stays offline.
- If a change affects the FastAPI surface, verify both automated tests and a manual `make serve` + `make scrape <target>` round-trip.

## Adding a Target or Transform

See the "Adding a target" and "Adding a transform" sections in [README.md](./README.md), and the practical walkthrough in [USAGE.md](./USAGE.md).

## Questions

Open an issue or discussion in the repository:

- https://github.com/RivoLink/loom/issues
- https://github.com/RivoLink/loom/discussions
