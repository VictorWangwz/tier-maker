"""Tests for template selection logic."""
from app.templates import select_template, TEMPLATES_DIR


def test_compact_template():
    path = select_template(2)
    assert path.name == "compact.html"
    assert path.exists()


def test_standard_template():
    path = select_template(5)
    assert path.name == "standard.html"
    assert path.exists()


def test_massive_template():
    path = select_template(8)
    assert path.name == "massive.html"
    assert path.exists()


def test_boundary_3():
    assert select_template(3).name == "compact.html"


def test_boundary_4():
    assert select_template(4).name == "standard.html"


def test_boundary_6():
    assert select_template(6).name == "standard.html"


def test_boundary_7():
    assert select_template(7).name == "massive.html"
