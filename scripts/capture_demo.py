"""Render the real TUI against synthetic filesystem metadata and REAL local model inference."""

import asyncio
from pathlib import Path

from jev_clean.ui.app import JevCleanApp


async def capture():
    assets = Path("docs/assets")
    assets.mkdir(parents=True, exist_ok=True)
    app = JevCleanApp(home=Path("/Users/demo"), demo=True)
    async with app.run_test(size=(132, 44)) as pilot:
        app.save_screenshot("welcome.svg", str(assets))
        for key, name in [("1", "clean"), ("2", "status")]:
            await pilot.press(key)
            for _ in range(200):
                await pilot.pause(0.1)
                if not app.busy and app.report is not None:
                    break
            else:
                raise RuntimeError("Real model demo did not complete")
            if name == "clean":
                await pilot.press("a")
            await pilot.pause(0.3)
            app.save_screenshot(name + ".svg", str(assets))
            if name == "clean":
                await pilot.press("b")
                await pilot.pause(0.3)
                app.save_screenshot("clean-breakdown.svg", str(assets))
                await pilot.press("b")
        await pilot.press("?")
        await pilot.pause(0.3)
        app.save_screenshot("keys.svg", str(assets))
    for svg in assets.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    print("Exported real TUI SVGs; metadata is synthetic, inference is real.")
    try:
        import cairosvg
        from PIL import Image

        frames = []
        for name in ["welcome", "clean", "clean-breakdown", "status", "keys"]:
            cairosvg.svg2png(url=str(assets / (name + ".svg")), write_to=str(assets / (name + ".png")))
            frame = Image.open(assets / (name + ".png")).convert("RGB")
            frame.thumbnail((1188, 792))
            frames.append(frame)
        frames[0].save(
            assets / "walkthrough.gif",
            save_all=True,
            append_images=frames[1:],
            duration=[1800, 4500, 4000, 4500, 3000],
            loop=0,
        )
        print("Created walkthrough.gif (screen sequence, not real-time playback).")
    except (ImportError, OSError):
        print("SVG assets created; install dev dependencies for PNG/GIF export.")


if __name__ == "__main__":
    asyncio.run(capture())
