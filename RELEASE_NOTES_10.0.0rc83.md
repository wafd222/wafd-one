# WAFD ONE 10.0.0 RC83

- Fixed Frappe Cloud package build failure by defining `__version__` in the actual Python package (`wafd_one/__init__.py`) used by Flit.
- Retained the required `pyproject.toml` Frappe v16 compatibility declaration.
- Retained the RC81 child DocType Python module fixes for the Iftar unit.
