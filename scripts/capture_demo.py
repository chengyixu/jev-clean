"""Capture the actual minimal TUI. Synthetic file metadata; real local model inference."""

import asyncio
from pathlib import Path

from jev_clean.ui.app import JevCleanApp


async def capture():
    assets = Path("docs/assets")
    assets.mkdir(parents=True, exist_ok=True)
    app = JevCleanApp(home=Path("/Users/demo"), demo=True)
    captured_logs = False
    original_trace = app.trace

    def trace(line):
        nonlocal captured_logs
        original_trace(line)
        if line.startswith("Laya explorer") and not captured_logs:
            captured_logs = True
            app.save_screenshot("logs.svg", str(assets))

    app.trace = trace
    async with app.run_test(size=(100, 30)) as pilot:
        app.save_screenshot("welcome.svg", str(assets))
        for key, name in [("1", "clean"), ("2", "status")]:
            await pilot.press(key)
            for _ in range(300):
                await pilot.pause(0.1)
                if not app.busy and app.report is not None:
                    break
            else:
                raise RuntimeError("Real model demo did not complete")
            if name == "clean":
                await pilot.press("a")
            await pilot.pause(0.2)
            app.save_screenshot(name + ".svg", str(assets))
            if name == "clean":
                await pilot.press("enter")
                await pilot.pause(0.2)
                app.save_screenshot("confirm.svg", str(assets))
                await pilot.press("n", "escape")
        await pilot.press("?")
        await pilot.pause(0.2)
        app.save_screenshot("keys.svg", str(assets))
    for svg in assets.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    print("Actual minimal TUI captured; synthetic data, real inference.")
    try:
        import cairosvg
        from PIL import Image

        frames = []
        for name in ["welcome", "logs", "clean", "confirm", "status", "keys"]:
            cairosvg.svg2png(url=str(assets / (name + ".svg")), write_to=str(assets / (name + ".png")))
            frame = Image.open(assets / (name + ".png")).convert("RGB")
            frame.thumbnail((1100, 720))
            frames.append(frame)
        frames[0].save(
            assets / "walkthrough.gif",
            save_all=True,
            append_images=frames[1:5],
            duration=[1500, 3000, 3500, 2500, 3500],
            loop=0,
        )
        print("Created screen-sequence walkthrough (not real-time playback).")
    except (ImportError, OSError):
        print("SVGs captured; PNG/GIF export needs Cairo and dev dependencies.")


if __name__ == "__main__":
    asyncio.run(capture())
