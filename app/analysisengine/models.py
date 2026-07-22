from dataclasses import dataclass
from .conditions import Condition
from .severity import Severity

@dataclass
class Rule:

    """
    Represents a single analysis rule.
    """
    name: str
    severity: Severity
    category: str
    condition: Condition
    diagnosis: str
    recommendation: str