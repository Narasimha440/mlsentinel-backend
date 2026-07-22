from abc import ABC, abstractmethod
from typing import Dict

class Condition(ABC):

    @abstractmethod
    def evaluate(self, metrics: Dict[str, float]) -> bool:
        pass


class LessThan(Condition):

    def __init__(self, metric: str, threshold: float):
        self.metric = metric
        self.threshold = threshold

    def evaluate(self, metrics: Dict[str, float]) -> bool:
        if self.metric not in metrics:
            return False
        return metrics[self.metric] < self.threshold

class GreaterThan(Condition):
    def __init__(self, metric: str, threshold: float):
        self.metric = metric
        self.threshold = threshold

    def evaluate(self, metrics: Dict[str, float]) -> bool:
        if self.metric not in metrics:
            return False
        return metrics[self.metric] > self.threshold

class Between(Condition):

    def __init__(self, metric: str, minimum: float, maximum: float):
        self.metric = metric
        self.minimum = minimum
        self.maximum = maximum

    def evaluate(self, metrics: Dict[str, float]) -> bool:

        if self.metric not in metrics:
            return False

        value = metrics[self.metric]

        return self.minimum <= value <= self.maximum

class GapExceeds(Condition):
    def __init__(self, metric_a: str, metric_b: str, max_gap: float):
        self.metric_a = metric_a
        self.metric_b = metric_b
        self.max_gap = max_gap

    def evaluate(self, metrics: Dict[str, float]) -> bool:
        if self.metric_a not in metrics or self.metric_b not in metrics:
            return False
        return (metrics[self.metric_a] - metrics[self.metric_b]) > self.max_gap

class AbsGapExceeds(Condition):
    def __init__(self, metric_a: str, metric_b: str, max_gap: float):
        self.metric_a = metric_a
        self.metric_b = metric_b
        self.max_gap = max_gap

    def evaluate(self, metrics: Dict[str, float]) -> bool:
        if self.metric_a not in metrics or self.metric_b not in metrics:
            return False
        return abs(metrics[self.metric_a] - metrics[self.metric_b]) > self.max_gap