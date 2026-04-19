"""Async client example: parallel fetch of multiple resources."""
import asyncio

from nopaque import AsyncNopaque


async def _collect(iterator):
    out = []
    async for item in iterator:
        out.append(item)
    return out


async def main() -> None:
    async with AsyncNopaque() as client:
        audio_task = asyncio.create_task(
            _collect(client.audio.list(limit=10))
        )
        profiles_task = asyncio.create_task(
            _collect(client.profiles.list(limit=10))
        )
        audio, profiles = await asyncio.gather(audio_task, profiles_task)
        print(f"{len(audio)} audio files, {len(profiles)} profiles")


if __name__ == "__main__":
    asyncio.run(main())
