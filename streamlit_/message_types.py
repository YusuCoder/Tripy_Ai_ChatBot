from dataclasses import dataclass
from typing import Literal, Optional, List

@dataclass
class Message:
    origin: Literal["human", "assistant"]
    message: Optional[str] = None
    image_bytes: Optional[bytes] = None
    image_labels: Optional[list[dict]] = None
    is_image_context: Optional[bool] = False 