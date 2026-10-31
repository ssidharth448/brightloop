"""Discount rules engine — in-memory store (no model changes required).

Rules are persisted to a JSON file in the project root so they survive
restarts but require no DB migration.
"""

import json
import os
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.schemas.discount import DiscountRuleCreate, DiscountRuleOut, DiscountRuleUpdate

# Persistent JSON file path — sits alongside the backend package
_RULES_FILE = Path(os.environ.get(
    "DISCOUNT_RULES_FILE",
    str(Path(__file__).resolve().parent.parent.parent / "discount_rules.json"),
))

# In-memory cache
_rules: dict[str, dict[str, Any]] = {}
_loaded = False


def _load() -> None:
    global _rules, _loaded
    if _loaded:
        return
    if _RULES_FILE.exists():
        try:
            raw = json.loads(_RULES_FILE.read_text(encoding="utf-8"))
            _rules = {r["id"]: r for r in raw}
        except Exception:
            _rules = {}
    _loaded = True


def _save() -> None:
    _RULES_FILE.write_text(
        json.dumps(list(_rules.values()), indent=2, default=str),
        encoding="utf-8",
    )


def _to_out(d: dict) -> DiscountRuleOut:
    return DiscountRuleOut(**d)


# ---------- CRUD ----------

def create_discount_rule(data: DiscountRuleCreate) -> DiscountRuleOut:
    _load()
    rule_id = str(uuid.uuid4())[:8]
    rule = data.model_dump()
    rule["id"] = rule_id
    rule["used_count"] = 0
    rule["is_active"] = True
    # Convert Decimal/date to serialisable types for JSON
    for k, v in rule.items():
        if isinstance(v, Decimal):
            rule[k] = str(v)
        elif isinstance(v, date):
            rule[k] = v.isoformat()
    _rules[rule_id] = rule
    _save()
    return _to_out(rule)


def list_discount_rules(active_only: bool = False) -> list[DiscountRuleOut]:
    _load()
    rules = list(_rules.values())
    if active_only:
        rules = [r for r in rules if r.get("is_active", True)]
    return [_to_out(r) for r in rules]


def get_discount_rule(rule_id: str) -> DiscountRuleOut | None:
    _load()
    rule = _rules.get(rule_id)
    return _to_out(rule) if rule else None


def update_discount_rule(rule_id: str, data: DiscountRuleUpdate) -> DiscountRuleOut | None:
    _load()
    rule = _rules.get(rule_id)
    if rule is None:
        return None
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        if isinstance(v, Decimal):
            rule[k] = str(v)
        elif isinstance(v, date):
            rule[k] = v.isoformat()
        else:
            rule[k] = v
    _rules[rule_id] = rule
    _save()
    return _to_out(rule)


def delete_discount_rule(rule_id: str) -> bool:
    _load()
    if rule_id not in _rules:
        return False
    del _rules[rule_id]
    _save()
    return True


# ---------- Evaluation ----------

def evaluate_discounts(
    subtotal: Decimal,
    quantity: int = 1,
    product_id: int | None = None,
    target: str = "all",
) -> Decimal:
    """Evaluate all active discount rules and return total discount amount.

    Applies the *best single discount* (highest value) that matches.
    """
    _load()
    today = date.today()
    best_discount = Decimal("0.00")

    for rule in _rules.values():
        if not rule.get("is_active", True):
            continue

        # Date validity
        start = rule.get("start_date")
        if start and date.fromisoformat(str(start)) > today:
            continue
        end = rule.get("end_date")
        if end and date.fromisoformat(str(end)) < today:
            continue

        # Max uses
        max_uses = int(rule.get("max_uses", 0))
        used = int(rule.get("used_count", 0))
        if max_uses > 0 and used >= max_uses:
            continue

        # Min purchase / quantity
        min_purchase = Decimal(str(rule.get("min_purchase", "0")))
        min_qty = int(rule.get("min_quantity", 0))
        if subtotal < min_purchase:
            continue
        if quantity < min_qty:
            continue

        # Target matching
        rule_applies = rule.get("applies_to", "all")
        if rule_applies == "product" and product_id is not None:
            if rule.get("product_id") and int(rule["product_id"]) != product_id:
                continue
        elif rule_applies != "all" and rule_applies != target:
            continue

        # Calculate discount
        dtype = rule.get("discount_type", "fixed")
        value = Decimal(str(rule.get("value", "0")))
        if dtype == "percentage":
            disc = (subtotal * value / Decimal("100")).quantize(Decimal("0.01"))
        else:
            disc = min(value, subtotal)

        if disc > best_discount:
            best_discount = disc

    return best_discount


def increment_usage(code: str) -> None:
    """Increment the used_count for a discount rule by code."""
    _load()
    for rule in _rules.values():
        if rule.get("code") == code:
            rule["used_count"] = int(rule.get("used_count", 0)) + 1
            _save()
            return
