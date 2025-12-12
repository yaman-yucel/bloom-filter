from pydantic import BaseModel, Field


class InitRequest(BaseModel):
    expected_items: int = Field(gt=0, description="Expected number of items")
    false_positive_rate: float = Field(gt=0, lt=1, description="Desired false positive rate")


class ItemRequest(BaseModel):
    item: str = Field(description="Item to add or check")


class CheckResponse(BaseModel):
    item: str
    exists: bool


class StatsResponse(BaseModel):
    size: int
    hash_count: int
    bits_set: int
    expected_items: int
    false_positive_rate: float
