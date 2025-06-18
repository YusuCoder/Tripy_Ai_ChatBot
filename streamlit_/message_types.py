from dataclasses import dataclass
from typing import Literal

@dataclass
class Message:
    origin: Literal["human", "assistant"]
    message: str