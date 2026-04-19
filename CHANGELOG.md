# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2026-04-19

### Fixed
- Cross-resource response envelope audit. The server uses resource-named
  keys for most list endpoints; the SDK previously assumed a standard
  `{items: [...]}` shape everywhere, so several list endpoints silently
  returned empty results. The following are now aligned with the server:
  - `client.mapping.runs(job_id)` — reads `runs` (was: `items`).
  - `client.mapping.paths(job_id)` — reads `rules` (was: `items`).
  - `client.batches.list()` / `list_page()` — reads `batches`.
  - `client.batches.runs(batch_id)` — reads `runs`.
  - `client.batches.list_runs()` — reads `runs`.
  - `client.sweeps.list()` / `list_page()` — reads `sweeps`.
  - `client.sweeps.runs(sweep_id)` — reads `runs`.
  - `client.sweeps.list_runs()` — reads `runs`.
  - `client.datasets.list()` / `list_page()` — reads `datasets`.
  - `client.load_testing.list()` / `list_page()` — reads `configs`.
  - `client.load_testing.list_runs()` — reads `runs`.
  - `client.scheduler.list()` / `list_page()` — reads `schedules`.
  - `client.audio.list()` / `list_page()` — reads `audioFiles`.
  - `client.profiles.list()` / `list_page()` — reads `profiles`.
  - `client.profiles.find_by_parameters()` — reads `profiles`.
- `client.load_testing.create()` and `client.load_testing.update()` now
  unwrap the server's `{config: {...}}` envelope. Previously, Pydantic
  validation failed when callers tried to read `.id` on the returned
  `LoadTest` because the SDK parsed the envelope itself as the entity.

### Changed (non-breaking)
- `SyncPaginator` / `AsyncPaginator` accept an `items_key: str = "items"`
  option so each resource can declare the key its list endpoint uses.
  Each paginator falls back to `"items"` if the declared key is missing,
  preserving forward-compatibility if the server ever standardizes.

## [0.1.2] - 2026-04-19

### Fixed
- `client.testing.runs.create()` now unwraps the server's `{message, run}`
  response envelope. Previously, validation failed because the SDK tried to
  parse the envelope itself as a `TestRun`, raising
  `pydantic.ValidationError: status — Field required`.
- `client.testing.configs.list()` / `list_page()`,
  `client.testing.jobs.list()` / `list_page()`, and
  `client.testing.runs.list()` / `list_page()` now read the server's actual
  response shape (`{configs: [...]}`, `{jobs: [...]}`, `{runs: [...]}`)
  rather than the never-emitted `{items: [...]}`. All three list methods
  previously returned empty results.

### Changed (breaking vs. 0.1.1)
- `TestRun.id` is now the canonical test-run identifier, matching the
  server's entity shape. The spurious `run_id` field (which was never
  populated) is removed. Callers should use `run.id` instead of
  `run.run_id`, and pass `run.id` to
  `client.testing.runs.wait_for_run()` and `get()`.
- `TestRun.status` is now `Optional[str]` because the newly-created run
  document may not include it until the orchestrator has picked up the
  job. Existing callers will not be affected.

## [0.1.1] - 2026-04-19

### Added
- `client.testing.runs.create()` now accepts `test_config_id=` for ad-hoc runs
  directly from a test config, in addition to the existing `job_id=`. Exactly
  one must be provided; mis-use raises `ValueError`. Matches the underlying
  `POST /testing/runs` endpoint, which has always accepted either.

## [0.1.0] - 2026-04-19

### Added
- Initial release.
- Synchronous (`Nopaque`) and asynchronous (`AsyncNopaque`) clients.
- Full coverage of the API-key-authenticated Nopaque REST API:
  mapping, profiles, testing (configs/jobs/runs), batches, sweeps,
  datasets, load testing, scheduler, enrichment, audio.
- Automatic pagination, polling helpers for long-running jobs,
  one-call audio upload/download.
- Method-aware retry with exponential jitter and `Retry-After` honor.
- Typed exception hierarchy.

[Unreleased]: https://github.com/nopaque/python-sdk/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/nopaque/python-sdk/releases/tag/v0.1.3
[0.1.2]: https://github.com/nopaque/python-sdk/releases/tag/v0.1.2
[0.1.1]: https://github.com/nopaque/python-sdk/releases/tag/v0.1.1
[0.1.0]: https://github.com/nopaque/python-sdk/releases/tag/v0.1.0
