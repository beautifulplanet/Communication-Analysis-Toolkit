"""
Locust load test for the Communication Analysis Toolkit API.

Usage (headless, CSV export):
    locust -f tests/locustfile.py --host http://localhost:8000 \
           --users 10 --spawn-rate 2 --run-time 60s --headless \
           --csv tests/load_results/tier1

Usage (web UI):
    locust -f tests/locustfile.py --host http://localhost:8000
"""
from __future__ import annotations

import random

from locust import HttpUser, between, task


class AnalysisUser(HttpUser):
    """Simulates a realistic user browsing case analysis data."""

    wait_time = between(1, 3)
    case_id: str | None = None

    def on_start(self) -> None:
        """Fetch available cases on spawn — only pick cases with data."""
        with self.client.get("/api/cases", catch_response=True, name="/api/cases") as resp:
            if resp.status_code == 200:
                cases = resp.json().get("cases", [])
                valid_cases = [c for c in cases if c.get("has_data", False)]
                if valid_cases:
                    self.case_id = random.choice(valid_cases)["case_id"]
            elif resp.status_code == 429:
                resp.success()  # Rate limited — expected under load

    # ------------------------------------------------------------------
    # Core endpoints (weighted by realistic usage patterns)
    # ------------------------------------------------------------------

    @task(3)
    def view_summary(self) -> None:
        """Most common action: user opens a case summary."""
        if self.case_id:
            with self.client.get(
                f"/api/cases/{self.case_id}/summary",
                catch_response=True,
                name="/api/cases/[id]/summary",
            ) as resp:
                if resp.status_code == 429:
                    resp.success()

    @task(2)
    def view_timeline(self) -> None:
        """Second most common: browse day-by-day timeline."""
        if self.case_id:
            with self.client.get(
                f"/api/cases/{self.case_id}/timeline",
                catch_response=True,
                name="/api/cases/[id]/timeline",
            ) as resp:
                if resp.status_code == 429:
                    resp.success()

    @task(1)
    def view_patterns(self) -> None:
        """Browse communication patterns."""
        if self.case_id:
            with self.client.get(
                f"/api/cases/{self.case_id}/patterns",
                catch_response=True,
                name="/api/cases/[id]/patterns",
            ) as resp:
                if resp.status_code == 429:
                    resp.success()

    @task(1)
    def view_hurtful(self) -> None:
        """Browse hurtful language breakdown."""
        if self.case_id:
            with self.client.get(
                f"/api/cases/{self.case_id}/hurtful",
                catch_response=True,
                name="/api/cases/[id]/hurtful",
            ) as resp:
                if resp.status_code == 429:
                    resp.success()

    @task(1)
    def view_cases(self) -> None:
        """Listing cases — lightweight endpoint."""
        with self.client.get("/api/cases", catch_response=True, name="/api/cases") as resp:
            if resp.status_code == 429:
                resp.success()

    @task(1)
    def check_health(self) -> None:
        """Health check — must stay fast even under load."""
        self.client.get("/api/health", name="/api/health")

    # ------------------------------------------------------------------
    # Edge cases — security & error handling under pressure
    # ------------------------------------------------------------------

    @task(1)
    def invalid_case_id(self) -> None:
        """Nonexistent case — should return 404, not crash."""
        with self.client.get(
            "/api/cases/NONEXISTENT_CASE_999/summary",
            catch_response=True,
            name="/api/cases/[invalid]/summary",
        ) as resp:
            if resp.status_code in (404, 429):
                resp.success()
            elif resp.status_code == 200:
                resp.failure("Should have returned 404 for invalid case")

    @task(1)
    def path_traversal_attempt(self) -> None:
        """Path traversal — must be blocked, not crash."""
        with self.client.get(
            "/api/cases/..%2F..%2F..%2Fetc%2Fpasswd/summary",
            catch_response=True,
            name="/api/cases/[traversal]/summary",
        ) as resp:
            if resp.status_code in (400, 403, 404, 422, 429):
                resp.success()
            elif resp.status_code == 200:
                resp.failure("PATH TRAVERSAL RETURNED 200 — SECURITY BUG")
