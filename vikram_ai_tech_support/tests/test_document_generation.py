"""Tests for generated project documents (PDF, PNG, Mermaid)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.generate_project_documents import (
    DATA_DIR,
    DEPARTMENTS,
    generate_all_documents,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Generate all documents once, into a temporary directory."""
    return generate_all_documents(tmp_path_factory.mktemp("docs"))


def test_pdf_exists_and_is_non_empty(generated: dict[str, Path]) -> None:
    pdf = generated["pdf"]
    assert pdf.exists()
    assert pdf.stat().st_size > 5_000  # a real multi-page document, not a stub


def test_pdf_has_valid_signature(generated: dict[str, Path]) -> None:
    header = generated["pdf"].read_bytes()[:5]
    assert header == b"%PDF-"


def test_pdf_is_multi_page(generated: dict[str, Path]) -> None:
    content = generated["pdf"].read_bytes()
    assert content.count(b"/Type /Page") >= 3 or content.count(b"/Type/Page") >= 3


def test_workflow_png_exists_and_is_non_empty(generated: dict[str, Path]) -> None:
    png = generated["png"]
    assert png.exists()
    assert png.stat().st_size > 10_000  # a rendered chart, not a blank image


def test_workflow_png_has_valid_signature(generated: dict[str, Path]) -> None:
    assert generated["png"].read_bytes()[:8] == PNG_SIGNATURE


def test_mermaid_file_exists(generated: dict[str, Path]) -> None:
    mmd = generated["mmd"]
    assert mmd.exists()
    assert mmd.stat().st_size > 0


def test_mermaid_contains_all_departments_and_flow(generated: dict[str, Path]) -> None:
    content = generated["mmd"].read_text(encoding="utf-8")
    assert "flowchart" in content
    for department in DEPARTMENTS:
        assert department in content
    assert "Manager Agent" in content
    assert "Clarification" in content


def test_committed_data_files_exist() -> None:
    """The repository ships pre-generated documents in data/."""
    assert (DATA_DIR / "development_plan.pdf").exists()
    assert (DATA_DIR / "workflow_chart.png").exists()
    assert (DATA_DIR / "workflow_chart.mmd").exists()
