"""Country RelationshipProviders for the dependency graph. Importing this package registers the
bundled providers (India, US). Add a country by writing a module here and calling register_provider.
"""
from __future__ import annotations

from . import india, us  # noqa: F401  (import side-effect: each module self-registers)
