"""Locust load test for the Communication Analysis Toolkit API."""
from locust import HttpUser, task, between
import random


class AnalysisUser(HttpUser):
    """Simulates a user browsing case data."""

    wait_time = between(1, 3)
    case_id: str | None = None

    def on_start(self) -> None:
        """Fetch available cases on spawn."""
        with self.client.get("/api/cases", catch_response=True) as resp:
            if resp.status_code == 200:
                cases = resp.json().get("cases", [])
                if cases:
                    self.case_id = random.choice(cases)["case_id"]

    @task(1)
    def view_cases(self) -> None:
        self.client.get("/api/cases")

    @task(3)
    def view_summary(self) -> None:
        if self.case_id:
            with self.client.get(
                f"/api/cases/{self.case_id}/summary", catch_response=True
            ) as resp:
                if resp.status_code == 429:
                    resp.success()  # Expected under load

    @task(2)
    def view_timeline(self) -> None:
        if self.case_id:
            with self.client.get(
                f"/api/cases/{self.case_id}/timeline", catch_response=True
            ) as resp:
                if resp.status_code == 429:
                    resp.success()

    @task(1)
    def check_health(self) -> None:
        self.client.get("/api/health")
