from abc import ABC, abstractmethod
from travelmate.models.state import TravelState


class BaseAgent(ABC):
    name: str = "BaseAgent"

    @abstractmethod
    def run(self, state: TravelState) -> TravelState:
        pass