from typing import Dict
from pydantic import BaseModel

class ReportRequest(BaseModel):
    project: str
    model: str
    metrics: Dict[str, float]