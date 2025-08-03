from pydantic import BaseModel


class Option(BaseModel):
    threshold: int
    healthy_range: int
    caution_range: int
    danger_range: int
