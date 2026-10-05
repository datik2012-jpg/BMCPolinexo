"""Validated memory-only export request contract."""
import re
from pydantic import BaseModel, Field, field_validator, model_validator
from .parser import FIELDS

class ExportEntry(BaseModel):
    id: str = Field(max_length=200)
    source_sheet: str = Field(max_length=32767)
    source_row: int = Field(ge=1, le=10000)
    original: dict[str, str]
    values: dict[str, str]
    issues: list[str] = Field(default_factory=list, max_length=100)
    excluded: bool = False
    baseline: dict[str, str] | None = None
    copied: bool = False

    @field_validator('original', 'values', 'baseline')
    @classmethod
    def complete_fields(cls, value):
        if value is not None and set(value) != set(FIELDS):
            raise ValueError('Invalid fields')
        return value


class ExportReport(BaseModel):
    instance_id: str
    report_date: str | None
    entries: list[ExportEntry] = Field(min_length=1, max_length=10000)
    warnings: list[str] = Field(default_factory=list, max_length=1000)


DETAILS = {'firstName': 'שם פרטי', 'lastName': 'שם משפחה', 'identity': 'תעודת זהות',
           'relationship': 'קרבה משפחתית', 'birthDate': 'תאריך לידה', 'gender': 'מין',
           'maritalStatus': 'מצב משפחתי', 'smoking': 'עישון'}


class ExportCustomer(BaseModel):
    id: str = Field(max_length=200)
    details: dict[str, str]
    report: ExportReport | None = None

    @field_validator('details')
    @classmethod
    def complete_details(cls, value):
        if set(value) != set(DETAILS):
            raise ValueError('Invalid details')
        return value


class ExportAgent(BaseModel):
    firstName: str = Field(default="", max_length=100)
    lastName: str = Field(default="", max_length=100)
    date: str = Field(default="", max_length=10)


class ExportRequest(BaseModel):
    agent: ExportAgent = Field(default_factory=ExportAgent)
    customers: list[ExportCustomer] = Field(min_length=1, max_length=50)
    selected_customer_id: str | None = None

    @model_validator(mode='after')
    def bounded(self):
        if len({c.id for c in self.customers}) != len(self.customers):
            raise ValueError('Duplicate customer')
        if sum(len(c.report.entries) for c in self.customers if c.report) > 20000:
            raise ValueError('Too many entries')
        # Excel truncates long text silently; reject instead of losing notes.
        def validate(value):
            if isinstance(value, str) and (len(value) > 32767 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]', value)):
                raise ValueError('Unsupported text')
            if isinstance(value, dict):
                for item in value.values():
                    validate(item)
            if isinstance(value, list):
                for item in value:
                    validate(item)
        validate(self.model_dump())
        if self.selected_customer_id is not None and self.selected_customer_id not in {c.id for c in self.customers}:
            raise ValueError("Unknown selection")
        return self



from .compact_export import create_export
