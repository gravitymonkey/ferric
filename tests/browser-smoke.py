#!/usr/bin/env python3
import subprocess
import sys
import time
import mimetypes
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


URL = "http://localhost:8080/public/index.html"


def wait_for_server(url: str, timeout_sec: int = 15) -> None:
  start = time.time()
  while time.time() - start < timeout_sec:
    try:
      with urlopen(url, timeout=2) as resp:
        if resp.status == 200:
          return
    except Exception:
      time.sleep(0.25)
  raise RuntimeError("dev server did not become ready in time")


def run_flow(page) -> None:
  page.goto(URL, wait_until="domcontentloaded")
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

  server = subprocess.Popen(
    ["python3", "-m", "http.server", "8080"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )

  try:
    wait_for_server(URL)
    failures = []
    with sync_playwright() as p:
      browsers = [
        ("chromium", p.chromium),
        ("firefox", p.firefox),
        ("webkit", p.webkit),
      ]

      for name, browser_type in browsers:
        try:
          browser = browser_type.launch(headless=True)
          page = browser.new_page()
          run_flow(page)
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
    server.terminate()
    try:
      server.wait(timeout=3)
    except Exception:
      server.kill()


if __name__ == "__main__":
  sys.exit(main())
