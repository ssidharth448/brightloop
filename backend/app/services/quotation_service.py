"""Quotation template service — in-memory store persisted to JSON."""

import json
import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.schemas.quotation import QuotationTemplateCreate, QuotationTemplateOut, QuotationTemplateUpdate
from app.services.subscription_service import create_subscription
from app.schemas.subscription import SubscriptionCreate

_TEMPLATES_FILE = Path(os.environ.get(
    "QUOTATION_TEMPLATES_FILE",
    str(Path(__file__).resolve().parent.parent.parent / "quotation_templates.json"),
))

_templates: dict[str, dict[str, Any]] = {}
_loaded = False


def _load() -> None:
    global _templates, _loaded
    if _loaded:
        return
    if _TEMPLATES_FILE.exists():
        try:
            raw = json.loads(_TEMPLATES_FILE.read_text(encoding="utf-8"))
            _templates = {t["id"]: t for t in raw}
        except Exception:
            _templates = {}
    _loaded = True


def _save() -> None:
    _TEMPLATES_FILE.write_text(
        json.dumps(list(_templates.values()), indent=2, default=str),
        encoding="utf-8",
    )


def _to_out(d: dict) -> QuotationTemplateOut:
    return QuotationTemplateOut(**d)


# ---------- CRUD ----------

def create_quotation_template(data: QuotationTemplateCreate) -> QuotationTemplateOut:
    _load()
    tmpl_id = str(uuid.uuid4())[:8]
    tmpl = data.model_dump()
    tmpl["id"] = tmpl_id
    tmpl["created_at"] = datetime.now(timezone.utc).isoformat()
    # Serialise Decimals
    for line in tmpl.get("product_lines", []):
        for k, v in line.items():
            if isinstance(v, Decimal):
                line[k] = str(v)
    _templates[tmpl_id] = tmpl
    _save()
    return _to_out(tmpl)


def list_quotation_templates() -> list[QuotationTemplateOut]:
    _load()
    return [_to_out(t) for t in _templates.values()]


def get_quotation_template(tmpl_id: str) -> QuotationTemplateOut | None:
    _load()
    tmpl = _templates.get(tmpl_id)
    return _to_out(tmpl) if tmpl else None


def update_quotation_template(tmpl_id: str, data: QuotationTemplateUpdate) -> QuotationTemplateOut | None:
    _load()
    tmpl = _templates.get(tmpl_id)
    if tmpl is None:
        return None
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        if k == "product_lines" and v is not None:
            serialised = []
            for line in v:
                ld = line if isinstance(line, dict) else line.model_dump()
                for lk, lv in ld.items():
                    if isinstance(lv, Decimal):
                        ld[lk] = str(lv)
                serialised.append(ld)
            tmpl[k] = serialised
        elif isinstance(v, Decimal):
            tmpl[k] = str(v)
        else:
            tmpl[k] = v
    _templates[tmpl_id] = tmpl
    _save()
    return _to_out(tmpl)


def delete_quotation_template(tmpl_id: str) -> bool:
    _load()
    if tmpl_id not in _templates:
        return False
    del _templates[tmpl_id]
    _save()
    return True


def convert_template_to_subscription(
    db: Session,
    template_id: str,
    customer_id: int,
    start_date: date | None = None,
):
    """Convert a quotation template into a live subscription.

    Returns the created Subscription ORM object.
    Raises ValueError if the template or plan doesn't exist.
    """
    _load()
    tmpl = _templates.get(template_id)
    if tmpl is None:
        raise ValueError(f"Quotation template '{template_id}' not found")

    plan_id = tmpl["plan_id"]
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise ValueError(f"Plan {plan_id} referenced by template not found")

    effective_start = start_date or date.today()
    sub_data = SubscriptionCreate(
        customer_id=customer_id,
        plan_id=plan_id,
        start_date=effective_start,
    )
    return create_subscription(db, sub_data)
