Overview
========

Welcome to the ``pypi-packaging-tutorial`` documentation. This project is a
minimal example of a Python package that demonstrates packaging, testing, and
continuous delivery best practices.

Getting Started
---------------

Install the package in editable mode so you can iterate locally::

   python -m pip install -e .[dev]

Then run the test suite to make sure everything is wired up::

   pytest

Key Modules
-----------

* :mod:`pypi_packaging_tutorial.core` — Simple utility helpers.
* :mod:`pypi_packaging_tutorial.divide` — Functions for dividing numbers.
* :mod:`pypi_packaging_tutorial.multiply` — Functions for multiplying numbers.

Workflow Highlights
-------------------

The repository ships with a reusable GitHub Actions workflow that:

* runs tests and security checks (pytest, coverage, Bandit, Black),
* generates SVG badges under ``badges/``,
* computes semantic version bumps, and
* publishes releases to PyPI via trusted publishing.

Use the :doc:`api` reference for full details of the available Python APIs.
