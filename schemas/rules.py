from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class RuleBase(BaseModel):
    name: str
    selector: str
    space_key: str
    page_id: str
    template_id: int | None = None
    auto_approve: bool = False

    @field_validator("name", "selector", "space_key", "page_id")
    @classmethod
    def ensure_non_empty(cls, value: str) -> str:
        clean_value = value.strip()
        if not clean_value:
            msg = "must not be empty"
            raise ValueError(msg)
        return clean_value

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            msg = "template_id must be a positive integer"
            raise ValueError(msg)
        return value


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = None
    selector: str | None = None
    space_key: str | None = None
    page_id: str | None = None
    template_id: int | None = None
    auto_approve: bool | None = None

    @field_validator("name", "selector", "space_key", "page_id")
    @classmethod
    def ensure_non_empty_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        clean_value = value.strip()
        if not clean_value:
            msg = "must not be empty"
            raise ValueError(msg)
        return clean_value

    @field_validator("template_id")
    @classmethod
    def validate_template_id_optional(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            msg = "template_id must be a positive integer"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def ensure_payload_not_empty(self) -> "RuleUpdate":
        if not any(
            getattr(self, field) is not None
            for field in (
                "name",
                "selector",
                "space_key",
                "page_id",
                "template_id",
                "auto_approve",
            )
        ):
            msg = "At least one field must be provided"
            raise ValueError(msg)
        return self


class RuleOut(RuleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
