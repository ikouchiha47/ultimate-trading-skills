"""The strategy zoo — every IStrategy provider, registered for the harness to rank.

Importing this package registers the built-in strategies so ``registry.strategies()``
and ``BacktestHarness.rank`` see them. Each provider earns its place against a null;
nothing here is privileged.
"""
from __future__ import annotations

from ..registry import register_strategy
from .bnf_flow_reversion import BnfFlowReversion
from .bnf_reversion import BnfReversion
from .nulls import BuyAndHoldBasket

# Register the testable providers in the zoo. The null is constructed per-basket by
# the harness (it needs the symbol list), so it is not a standalone zoo entry.
register_strategy(BnfReversion())
register_strategy(BnfFlowReversion())

__all__ = ["BnfReversion", "BnfFlowReversion", "BuyAndHoldBasket"]
