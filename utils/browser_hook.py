import os
import re
import shutil
from pathlib import Path
from conf import LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH


def _find_system_chrome() -> str | None:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _find_cached_ms_playwright_chromium(headless: bool) -> str | None:
    local_app = os.environ.get("LOCALAPPDATA", "")
    if not local_app:
        return None
    ms_dir = Path(local_app) / "ms-playwright"
    if not ms_dir.is_dir():
        return None

    def _ver(p: Path) -> int:
        m = re.search(r"(\d+)$", p.name)
        return int(m.group(1)) if m else 0

    if headless:
        shells = sorted(ms_dir.glob("chromium_headless_shell-*"), key=_ver, reverse=True)
        for d in shells:
            exe = d / "chrome-headless-shell-win64" / "chrome-headless-shell.exe"
            if exe.is_file():
                return str(exe)

    chromes = sorted(ms_dir.glob("chromium-*"), key=_ver, reverse=True)
    for d in chromes:
        exe = d / "chrome-win64" / "chrome.exe"
        if exe.is_file():
            return str(exe)
    return None


def resolve_chromium_launch_kwargs(playwright=None, headless: bool | None = None, args: list[str] | None = None) -> dict:
    is_headless = LOCAL_CHROME_HEADLESS if headless is None else headless
    options: dict = {"headless": is_headless}
    if args:
        options["args"] = args

    if LOCAL_CHROME_PATH and os.path.exists(LOCAL_CHROME_PATH):
        options["executable_path"] = LOCAL_CHROME_PATH
        return options

    if playwright is not None:
        try:
            bundled = playwright.chromium.executable_path
            if bundled and os.path.exists(bundled):
                return options
        except Exception:
            pass

    if _find_system_chrome():
        options["channel"] = "chrome"
        return options

    cached = _find_cached_ms_playwright_chromium(is_headless)
    if cached:
        options["executable_path"] = cached
    return options


def get_browser_options():
    options = {
        'headless': LOCAL_CHROME_HEADLESS,
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--lang=zh-CN',
            '--disable-infobars',
            '--start-maximized',
            '--no-sandbox',
            '--disable-web-security'
        ]
    }
    if LOCAL_CHROME_PATH:
        options['executable_path'] = LOCAL_CHROME_PATH
    return options
