# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/nopaque/python-sdk/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/nopaque/python-sdk/releases/tag/v0.1.1
[0.1.0]: https://github.com/nopaque/python-sdk/releases/tag/v0.1.0
