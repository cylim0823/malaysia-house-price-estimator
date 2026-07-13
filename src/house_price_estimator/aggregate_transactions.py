"""Compatibility imports for model bundles created before the generic refactor.

New code should import :mod:`house_price_estimator.data_pipeline`.
"""

from .data_pipeline import *  # noqa: F401,F403
