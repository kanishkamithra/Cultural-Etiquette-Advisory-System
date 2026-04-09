from __future__ import annotations

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str


class SessionOut(BaseModel):
    token: str
    user: UserOut


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class CultureIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=500)


class ScenarioIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)


class RuleIn(BaseModel):
    culture_id: int
    scenario_id: int
    do_text: str = Field(min_length=1, max_length=500)
    dont_text: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=1, max_length=500)
    safe_alternative: str = Field(min_length=1, max_length=500)
    severity: str


class AdviceRequest(BaseModel):
    culture_id: int
    scenario_id: int
    formality: str = Field(default="formal", pattern="^(formal|informal)$")
    setting: str = Field(default="business", pattern="^(business|casual)$")
    relationship: str = Field(default="client", pattern="^(friend|client|boss|host|colleague|elder|stranger)$")
    user_notes: str = Field(default="", max_length=500)


class SaveAdviceIn(BaseModel):
    culture_id: int
    scenario_id: int
    culture_name: str
    scenario_name: str
    risk_label: str
    risk_percent: int
    generated_at: str


class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)


class FavoriteIn(BaseModel):
    culture_id: int
    scenario_id: int


class CompareRequest(BaseModel):
    left_culture_id: int
    right_culture_id: int
    scenario_id: int


class MistakeAlertRequest(BaseModel):
    culture_id: int
    scenario_id: int | None = None
    action_text: str = Field(min_length=3, max_length=500)


class CommunityTipIn(BaseModel):
    culture_id: int
    scenario_id: int | None = None
    title: str = Field(min_length=3, max_length=160)
    tip_text: str = Field(min_length=5, max_length=1000)


class NlpAdviceRequest(BaseModel):
    query: str = Field(min_length=4, max_length=500)


class SimulationRequest(BaseModel):
    culture_id: int
    scenario_id: int
    step: int = Field(ge=1, le=3)
    choice: str = Field(min_length=3, max_length=300)
    formality: str = Field(default="formal", pattern="^(formal|informal)$")
    setting: str = Field(default="business", pattern="^(business|casual)$")
    relationship: str = Field(default="client", pattern="^(friend|client|boss|host|colleague|elder|stranger)$")
