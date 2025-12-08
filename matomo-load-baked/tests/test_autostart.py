import asyncio
from pathlib import Path

from test_backfill import load_loader


def test_wait_for_start_signal_skips_when_enabled(monkeypatch):
    loader = load_loader()
    monkeypatch.setattr(loader, "AUTO_START", True)
    asyncio.run(asyncio.wait_for(loader.wait_for_start_signal(), timeout=0.1))


def test_wait_for_start_signal_blocks_until_file(tmp_path: Path, monkeypatch):
    signal_path = tmp_path / "loadgen.start"
    loader = load_loader()
    monkeypatch.setattr(loader, "AUTO_START", False)
    monkeypatch.setattr(loader, "START_SIGNAL_FILE", str(signal_path))
    monkeypatch.setattr(loader, "START_CHECK_INTERVAL", 0.01)

    async def create_signal():
        await asyncio.sleep(0.02)
        signal_path.write_text("start")

    async def orchestrate():
        waiter = asyncio.create_task(loader.wait_for_start_signal())
        creator = asyncio.create_task(create_signal())
        await asyncio.gather(waiter, creator)

    asyncio.run(asyncio.wait_for(orchestrate(), timeout=1))
    assert not signal_path.exists()
