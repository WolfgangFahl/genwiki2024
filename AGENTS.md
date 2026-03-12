# AGENTS.md - Development Guidelines for genwiki2024

## Project Overview
This is a Python project for semantification of genealogy data. It uses:
- **Build system**: hatchling (via pyproject.toml)
- **Testing**: unittest (built-in), green, tox
- **Code formatting**: black, isort

## Commands

### Running Tests
```bash
# Run all tests (unittest discover)
python -m unittest discover

# Run a single test module
python -m unittest tests.test_location

# Run a specific test class
python -m unittest tests.test_location.TestLocations

# Run a specific test method
python -m unittest tests.test_location.TestLocations.test_coords

# Run tests with green (colored output)
./scripts/test -g

# Run tests module by module
./scripts/test -m

# Run tests with tox
./scripts/test -t
```

### Code Quality
```bash
# Run checkov static analysis
checkov -p genwiki2024 --local

# Format code with black and sort imports with isort
./scripts/blackisort
```

### Building
```bash
# Build the package
pip install -e .

# Create a wheel
pip install build
python -m build
```

## Code Style Guidelines

### Imports
- Use isort to organize imports automatically
- Order: stdlib → third-party → local application
- Example from `genwiki/locator.py`:
```python
import logging
import os
from collections import Counter
from typing import Any, Dict, List

import geocoder
from ez_wikidata.wdsearch import WikidataSearch
from geopy.distance import geodesic

from genwiki.genwiki_paths import GenWikiPaths
from genwiki.gov_api import GOV_API
```

### Formatting
- Use **black** with default settings (line length 88)
- Run `./scripts/blackisort` before committing

### Type Hints
- Use type hints for function parameters and return types
- Common types: `Dict`, `List`, `Any`, `Optional`, `Tuple`
- Example:
```python
def locate(self, gov_id: str) -> Dict[str, str]:
    ...
```

### Naming Conventions
- **Functions/variables**: snake_case (`get_coordinates`, `items`)
- **Classes**: PascalCase (`Locator`, `GenealogyBasetest`)
- **Constants**: UPPER_SNAKE_CASE
- Be descriptive: `lookup_wikidata_id_by_geoid` not `lookup`

### Docstrings
- Use docstrings for classes and public methods
- Format from `tests/test_location.py`:
```python
def test_coords(self):
    """
    test getting coordinates for items
    """
```
- File-level docstring format:
```python
"""
Created on 2024-08-25

@author: wf
"""
```

### Error Handling
- Use specific exception types (`ValueError`, `KeyError`)
- Log warnings appropriately:
```python
if not gov_lat or not gov_lon:
    msg = "Gov object does not have valid coordinates"
    logging.warn(msg)
```
- Raise exceptions with descriptive messages:
```python
raise ValueError(f"invalid geo_id_kind {geoid_kind}")
raise ValueError(f"wikidata has multiple entries for {param_name}:{geo_id}")
```

### Testing Conventions
- Test classes inherit from `GenealogyBasetest` (which extends `ngwidgets.basetest.Basetest`)
- Set up test fixtures in `setUp` method:
```python
def setUp(self, debug=False, profile=True):
    GenealogyBasetest.setUp(self, debug=debug, profile=profile)
    self.locator = Locator(debug=debug)
```
- Use `self.assertEqual`, `self.assertIsNotNone` for assertions
- Debug output with `print()` for development, conditional on `self.debug`

### Logging
- Use the logging module:
```python
import logging
logging.warn(msg)  # for warnings
logging.error(msg)  # for errors
```

### File Organization
- Main package: `genwiki/`
- Tests: `tests/`
- Examples/data: `genwiki_examples/`
- Scripts: `scripts/`

### Configuration
- Project metadata in `pyproject.toml`
- Version defined in `genwiki/__init__.py`
- Dependencies managed via pyproject.toml

## Dependencies
- `pybasemkit` - base utilities
- `py-3rdparty-mediawiki` - MediaWiki interaction
- `py-ez-wikidata` - Wikidata access
- `mwparserfromhell` - template parsing
- `ngwidgets` - UI components
- `rdflib-endpoint` - RDF/graph support

## Test Dependencies
- `green` - colored test runner
- `owlready2` - ontology testing
