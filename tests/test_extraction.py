import pytest
from pydantic import ValidationError

from change_order_extractor.schemas import ChangeOrder


def field(value, evidence=None, confidence=0.0):
    if value is None:
        return {
            "value": None,
            "evidence": None,
            "confidence": 0.0,
        }

    return {
        "value": value,
        "evidence": evidence,
        "confidence": confidence,
    }


def test_valid_change_order():
    result = ChangeOrder.model_validate({
        "change_order_id": field("104", "CHANGE ORDER #104", 0.99),
        "project_name": field(
            "Riverside Office", "Project: Riverside Office", 0.99
        ),
        "description": field(
            "Additional electrical work",
            "Description: Additional electrical work",
            0.98,
        ),
        "change_reason": field(
            "Client request",
            "The client requested additional electrical work.",
            0.95,
        ),
        "cost_impact": {
            "amount": field(4500, "$4,500 USD", 0.99),
            "currency": field("USD", "$4,500 USD", 0.99),
        },
        "schedule_impact_days": field(
            10, "Schedule Impact: 10 days", 0.99
        ),
        "approval_status": field(
            "pending", "Approval Status: Pending", 0.99
        ),
        "review_required": False,
        "review_reasons": [],
    })

    assert result.change_order_id.value == "104"
    assert result.project_name.value == "Riverside Office"
    assert result.cost_impact.amount.value == 4500
    assert result.schedule_impact_days.value == 10
    assert result.approval_status.value == "pending"
    assert result.cost_impact.amount.evidence == "$4,500 USD"


def test_missing_values_are_allowed():
    result = ChangeOrder.model_validate({
        "cost_impact": {},
    })

    assert result.cost_impact.amount.value is None
    assert result.cost_impact.amount.confidence == 0
    assert result.cost_impact.currency.value is None
    assert result.schedule_impact_days.value is None
    assert result.approval_status.value is None
    assert result.approval_status.confidence == 0


def test_invalid_approval_status_is_rejected():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "approval_status": field(
                "maybe", "Approval Status: Maybe", 0.8
            ),
        })


def test_extracted_value_requires_evidence():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "change_order_id": {
                "value": "104",
                "evidence": None,
                "confidence": 0.9,
            },
        })


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "change_order_id": field(
                "104", "CHANGE ORDER #104", 1.5
            ),
        })


def test_missing_value_must_have_zero_confidence():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "change_order_id": {
                "value": None,
                "evidence": None,
                "confidence": 0.5,
            },
        })


def test_review_reasons_are_preserved():
    result = ChangeOrder.model_validate({
        "review_required": True,
        "review_reasons": ["Cost amount is ambiguous."],
    })

    assert result.review_required is True
    assert "Cost amount is ambiguous." in result.review_reasons


def test_missing_evidence_is_not_allowed_for_extracted_value():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "approval_status": {
                "value": "pending",
                "evidence": "   ",
                "confidence": 0.8,
            },
        })


def test_structured_cost_conflict_is_preserved():
    result = ChangeOrder.model_validate({
        "review_required": True,
        "review_reasons": ["The final cost is ambiguous."],
        "conflicts": [
            {
                "field": "cost_impact.amount",
                "candidates": [4500, 5200],
                "evidence": [
                    "The proposed change is $4,500 USD.",
                    "The updated total for this change is $5,200 USD.",
                ],
            }
        ],
    })

    conflict = result.conflicts[0]
    assert conflict.field == "cost_impact.amount"
    assert conflict.candidates == [4500, 5200]
    assert len(conflict.evidence) == 2
    assert result.review_required is True


def test_conflict_requires_human_review():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "review_required": False,
            "conflicts": [
                {
                    "field": "schedule_impact_days",
                    "candidates": [10, 15],
                    "evidence": [
                        "Work is expected to add 10 days.",
                        "Estimated impact is 15 days.",
                    ],
                }
            ],
        })


def test_conflict_requires_matching_evidence():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "review_required": True,
            "review_reasons": ["Schedule impact is ambiguous."],
            "conflicts": [
                {
                    "field": "schedule_impact_days",
                    "candidates": [10, 15],
                    "evidence": ["Work is expected to add 10 days."],
                }
            ],
        })


def test_conflict_requires_distinct_candidates():
    with pytest.raises(ValidationError):
        ChangeOrder.model_validate({
            "review_required": True,
            "review_reasons": ["Values conflict."],
            "conflicts": [
                {
                    "field": "cost_impact.amount",
                    "candidates": [4500, 4500],
                    "evidence": [
                        "The proposed change is $4,500 USD.",
                        "The updated total is $4,500 USD.",
                    ],
                }
            ],
        })
