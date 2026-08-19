"""Browser-level coverage for the quick tester review flow."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REVIEW_IDS = [
    "G1",
    "G2",
    "Q1",
    "Q2",
    "Q3",
    "Q4",
    "Q5",
    "Q6",
    "Q7",
    "product-reference",
    "Q8",
    "Q9",
    "Q10",
    "Q11",
    "Q12",
    "optional-evidence",
]


def _free_port() -> int:
    """Reserve an available local TCP port for the browser server."""
    with socket.socket() as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        return int(server_socket.getsockname()[1])


@pytest.fixture(scope="module")
def server(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Run the ASGI app against isolated response storage."""
    port = _free_port()
    response_path = tmp_path_factory.mktemp("browser-responses") / "responses.jsonl"
    environment = os.environ.copy()
    environment.update(
        {
            "APP_SESSION_SECRET": "browser-test-session-secret",
            "RESPONSE_PATH": str(response_path),
            "SURVEY_MANIFEST_PATH": str(ROOT / "data/survey-manifest.json"),
            "ALLOWED_TESTERS_PATH": str(ROOT / "config/allowed-testers.json"),
            "SECURE_COOKIES": "false",
        }
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                if httpx.get(f"{base_url}/health", timeout=0.2).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        else:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"server did not start: {stderr}")
        yield base_url
    finally:
        process.terminate()
        process.wait(timeout=10)


def _complete_review(page: Page) -> None:
    """Complete every review point with the quickest judgment."""
    for review_id in EXPECTED_REVIEW_IDS:
        expect(page.locator("[data-review-id]")).to_have_attribute(
            "data-review-id", review_id
        )
        page.get_by_role("radio", name="Good question").check()
        page.locator("#next").click()


def test_tester_can_complete_review_on_desktop_and_mobile(server: str) -> None:
    """Approved testers can finish with required judgments and no comments."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(server)
        expect(page.get_by_role("heading", name="Global survey review")).to_be_visible()

        page.get_by_label("Approved tester email").fill("gcarletto@worldbank.org")
        page.get_by_role("button", name="Continue").click()
        expect(
            page.get_by_role("heading", name="Make every question earn its place.")
        ).to_be_visible()
        page.get_by_role("button", name="Start review").click()
        expect(page.locator("[data-review-id]")).to_have_attribute(
            "data-review-id", "G1"
        )
        expect(page.get_by_role("button", name="Next")).to_be_disabled()

        _complete_review(page)
        expect(page.get_by_role("heading", name="One last thing")).to_be_visible()
        page.get_by_role("button", name="Submit feedback").click()
        expect(page.get_by_role("heading", name="Feedback recorded")).to_be_visible()

        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto(server)
        expect(
            mobile_page.get_by_role("heading", name="Global survey review")
        ).to_be_visible()
        assert mobile_page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        browser.close()
