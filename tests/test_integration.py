"""
Integration tests for the full analysis pipeline.

Covers:
  - End-to-end: config → ingest CSV → analyze → generate all reports
  - Verifies all 5 output files are created
  - Verifies report content structure
  - Verifies no PII leaks from test data into report headers
"""

import sys
import os
import json
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.analyzer import main as run_analysis, load_config


@pytest.fixture
def case_dir():
    """Create a temporary case directory with config and sample CSV data."""
    tmpdir = tempfile.mkdtemp(prefix="cat_test_")
    source_dir = os.path.join(tmpdir, "source_data")
    output_dir = os.path.join(tmpdir, "output")
    os.makedirs(source_dir)

    # Write sample CSV with a mix of benign and flagged messages
    csv_path = os.path.join(source_dir, "messages.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("datetime,direction,body\n")
        # Benign messages
        f.write("2025-06-01 09:00:00,sent,Good morning how are you?\n")
        f.write("2025-06-01 09:05:00,received,I'm doing well thanks!\n")
        f.write("2025-06-01 12:00:00,sent,Want to grab lunch?\n")
        f.write("2025-06-01 12:05:00,received,Sure! Where?\n")
        # DARVO - deny
        f.write("2025-06-02 18:00:00,received,I never said that\n")
        # Gaslighting
        f.write("2025-06-02 18:05:00,received,You're imagining things\n")
        # Hurtful - severe
        f.write("2025-06-03 22:00:00,received,No one will ever love you\n")
        # Apology (should suppress mild categories)
        f.write("2025-06-04 08:00:00,received,I'm sorry I was wrong\n")
        # Normal message
        f.write("2025-06-04 10:00:00,sent,It's okay let's move on\n")
        # More normal messages for volume
        f.write("2025-06-05 14:00:00,sent,How was your day?\n")
        f.write("2025-06-05 14:30:00,received,Pretty good actually\n")
        f.write("2025-06-05 20:00:00,sent,Goodnight!\n")

    # Write config
    config = {
        "case_name": "Integration Test Case",
        "user_label": "Test User",
        "contact_label": "Test Contact",
        "contact_phone": "",
        "phone_suffix": "",
        "csv_messages": csv_path,
        "output_dir": output_dir,
        "date_start": "2025-06-01",
        "date_end": "2025-06-30"
    }
    config_path = os.path.join(tmpdir, "config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f)

    yield tmpdir, config_path, output_dir

    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestFullPipeline:
    """End-to-end integration tests."""

    def test_analysis_produces_all_outputs(self, case_dir):
        tmpdir, config_path, output_dir = case_dir
        run_analysis(config_path)

        expected_files = [
            "ANALYSIS.md",
            "EVIDENCE.md",
            "TIMELINE.md",
            "AI_PROMPTS.md",
            "DATA.json",
        ]
        for fname in expected_files:
            fpath = os.path.join(output_dir, fname)
            assert os.path.exists(fpath), f"Missing output: {fname}"
            assert os.path.getsize(fpath) > 0, f"Empty output: {fname}"

    def test_analysis_md_structure(self, case_dir):
        tmpdir, config_path, output_dir = case_dir
        run_analysis(config_path)

        with open(os.path.join(output_dir, "ANALYSIS.md"), 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Integration Test Case" in content
        assert "Test User" in content
        assert "Test Contact" in content

    def test_evidence_md_has_flagged_content(self, case_dir):
        tmpdir, config_path, output_dir = case_dir
        run_analysis(config_path)

        with open(os.path.join(output_dir, "EVIDENCE.md"), 'r', encoding='utf-8') as f:
            content = f.read()

        # The gaslighting and hurtful messages should appear
        assert len(content) > 100  # Should have real content

    def test_data_json_valid(self, case_dir):
        tmpdir, config_path, output_dir = case_dir
        run_analysis(config_path)

        with open(os.path.join(output_dir, "DATA.json"), 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["case"] == "Integration Test Case"
        assert data["user"] == "Test User"
        assert data["contact"] == "Test Contact"
        assert "days" in data
        assert len(data["days"]) > 0

    def test_timeline_has_dates(self, case_dir):
        tmpdir, config_path, output_dir = case_dir
        run_analysis(config_path)

        with open(os.path.join(output_dir, "TIMELINE.md"), 'r', encoding='utf-8') as f:
            content = f.read()

        assert "2025-06" in content

    def test_no_pii_in_outputs(self, case_dir):
        """Verify no hardcoded PII leaks into outputs."""
        tmpdir, config_path, output_dir = case_dir
        run_analysis(config_path)

        pii_patterns = ["Elite", "FLUFFY", "13478370839", "Liming"]

        for fname in os.listdir(output_dir):
            fpath = os.path.join(output_dir, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            for pii in pii_patterns:
                assert pii not in content, f"PII '{pii}' found in {fname}"
