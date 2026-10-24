
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


ConflictField = Literal[
    "change_order_id",
    "project_name",
    "description",
    "change_reason",
    "cost_impact.amount",
    "cost_impact.currency",
    "schedule_impact_days",
    "approval_status",
]


class ExtractedField(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    value: T | None = None
    evidence: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_evidence(self):
        if self.value is None:
            if self.evidence is not None:
                raise ValueError(
                    "Missing values must not have evidence."
                )

            if self.confidence != 0:
                raise ValueError(
                    "Missing values must have confidence 0."
                )

        elif not self.evidence or not self.evidence.strip():
            raise ValueError(
                "Extracted values require source evidence."
            )

        return self


class CostImpact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: ExtractedField[float] = Field(
        default_factory=ExtractedField
    )
    currency: ExtractedField[str] = Field(
        default_factory=ExtractedField
    )


class FieldConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: ConflictField
    candidates: list[str | int | float] = Field(min_length=2)
    evidence: list[str] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_conflict(self):
        if len(self.candidates) != len(self.evidence):
            raise ValueError(
                "Each conflict candidate must have matching evidence."
            )

        if len(set(map(str, self.candidates))) != len(self.candidates):
            raise ValueError(
                "Conflict candidates must be distinct."
            )

        if any(
            not item.strip()
            for item in self.evidence
        ):
            raise ValueError(
                "Conflict evidence cannot be empty."
            )

        return self


class ChangeOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_order_id: ExtractedField[str] = Field(
        default_factory=ExtractedField
    )
    project_name: ExtractedField[str] = Field(
        default_factory=ExtractedField
    )
    description: ExtractedField[str] = Field(
        default_factory=ExtractedField
    )
    change_reason: ExtractedField[str] = Field(
        default_factory=ExtractedField
    )

    cost_impact: CostImpact = Field(
        default_factory=CostImpact
    )

    schedule_impact_days: ExtractedField[int] = Field(
        default_factory=ExtractedField
    )

    approval_status: ExtractedField[
        Literal["approved", "pending", "rejected", "unknown"]
    ] = Field(
        default_factory=ExtractedField
    )

    review_required: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    conflicts: list[FieldConflict] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review_flags(self):
        if self.conflicts and not self.review_required:
            raise ValueError(
                "Structured conflicts require human review."
            )

        if self.review_required and not self.review_reasons:
            raise ValueError(
                "Human review requires at least one review reason."
            )

        return self
