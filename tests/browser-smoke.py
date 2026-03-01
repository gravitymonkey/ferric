#!/usr/bin/env python3
import subprocess
import sys
import time
import mimetypes
import os
import socket
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


def find_free_port() -> int:
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    return int(sock.getsockname()[1])


def wait_for_server(url: str, timeout_sec: int = 20) -> None:
  start = time.time()
  while time.time() - start < timeout_sec:
    try:
      with urlopen(url, timeout=2) as resp:
        if resp.status == 200:
          return
    except Exception:
      time.sleep(0.25)
  raise RuntimeError("dev server did not become ready in time")


def run_flow(page, url: str) -> None:
  page.goto(url, wait_until="domcontentloaded")
  page.locator("#status").filter(has_text="Loaded").wait_for(timeout=10000)
  page.locator("#track-list li button").first.click()

  page.locator("#show-now-playing").click()
  page.locator("#np-title").filter(has_text="Scars").wait_for(timeout=10000)
  page.locator("#play-pause[data-state='playing']").wait_for(timeout=10000)

  # While track 1 is playing, select track 2 from list and ensure view switches back
  # to now-playing with the newly selected track.
  page.locator("#show-list").click()
  page.locator("#track-list li").nth(1).locator("button").click()
  page.locator("#np-title").filter(has_text="Neon Harbor").wait_for(timeout=10000)
  page.locator("#play-pause[data-state='playing']").wait_for(timeout=10000)

  page.locator("#play-pause").click()
  page.locator("#play-pause[data-state='paused']").wait_for(timeout=5000)

  page.locator("#np-scrubber").evaluate(
    """el => {
      el.value = "30";
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    }"""
  )
  page.locator("#next").click()
  page.locator("#np-title").filter(has_text="Static Bloom").wait_for(timeout=10000)


def main() -> int:
  mimetypes.add_type("text/javascript", ".mjs")
  mimetypes.add_type("application/vnd.apple.mpegurl", ".m3u8")
  mimetypes.add_type("video/mp2t", ".ts")

  backend_port = find_free_port()
  frontend_port = find_free_port()
  health_url = f"http://127.0.0.1:{backend_port}/api/v1/health"
  url = f"http://127.0.0.1:{frontend_port}/public/index.html"

  backend = subprocess.Popen(
    ["python3", "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(backend_port)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  frontend = subprocess.Popen(
    ["python3", "scripts/dev_server.py"],
    env={
      **os.environ,
      "PORT": str(frontend_port),
      "BACKEND_ORIGIN": f"http://127.0.0.1:{backend_port}",
    },
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )

  try:
    wait_for_server(health_url)
    wait_for_server(url)
    failures = []
    with sync_playwright() as p:
      browsers = [
        ("chromium", p.chromium),
        ("firefox", p.firefox),
        ("webkit", p.webkit),
      ]

      for name, browser_type in browsers:
        try:
          launch_kwargs = {"headless": True}
          if name == "chromium":
            launch_kwargs["args"] = ["--autoplay-policy=no-user-gesture-required"]
          elif name == "firefox":
            launch_kwargs["firefox_user_prefs"] = {"media.autoplay.default": 0}

          browser = browser_type.launch(**launch_kwargs)
          page = browser.new_page()
          run_flow(page, url)
          browser.close()
          print(f"PASS: {name} smoke flow")
        except Exception as exc:
          failures.append((name, str(exc)))
          print(f"FAIL: {name} smoke flow -> {exc}")

    if failures:
      print("\nBrowser smoke failures:")
      for name, msg in failures:
        print(f"- {name}: {msg}")
      return 1

    print("PASS: browser smoke across chromium/firefox/webkit")
    return 0
  finally:
    frontend.terminate()
    backend.terminate()
    try:
      frontend.wait(timeout=3)
      backend.wait(timeout=3)
    except Exception:
      frontend.kill()
      backend.kill()


if __name__ == "__main__":
  sys.exit(main())
