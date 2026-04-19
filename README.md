# nopaque - Python SDK for Nopaque

Official Python client for the [Nopaque](https://nopaque.co.uk) API.

## Install

```bash
pip install nopaque
```

## Quick start

```python
from nopaque import Nopaque

client = Nopaque(api_key="nop_live_...")   # or set NOPAQUE_API_KEY

# Create a mapping job and wait for it to complete
job = client.mapping.create(
    name="Main IVR",
    phone_number="+441234567890",
    mapping_mode="dtmf",
)
client.mapping.start(job.id)
final = client.mapping.wait_for_complete(job.id)
print(final.status)

# List audio files with automatic pagination
for audio in client.audio.list():
    print(audio.id, audio.file_name)

client.close()
```

## Async

```python
import asyncio
from nopaque import AsyncNopaque

async def main():
    async with AsyncNopaque() as client:
        job = await client.mapping.get("map_abc123")
        print(job.status)

asyncio.run(main())
```

## Features

- Full coverage of the Nopaque REST API via API-key auth
- Typed Pydantic v2 models for every request and response
- Paired sync (`Nopaque`) and async (`AsyncNopaque`) clients
- Automatic pagination for list endpoints
- Polling helpers for long-running jobs (`wait_for_complete`)
- One-call audio upload/download wrapping the presigned-URL flow
- Method-aware retry with exponential jitter and `Retry-After` honor
- Typed exception hierarchy (`NotFoundError`, `RateLimitError`, etc.)

## Documentation

Full reference: <https://nopaque.co.uk/docs/sdks>

## Authentication

Pass your API key to the client:

```python
Nopaque(api_key="nop_live_...")
```

Or set the environment variable:

```bash
export NOPAQUE_API_KEY=nop_live_...
```

API keys are workspace-scoped and subject to per-minute rate limits based on
your subscription tier. Free tier cannot use API keys.

## Requirements

- Python 3.9+
- `httpx >= 0.27`, `pydantic >= 2.6`

## License

MIT
