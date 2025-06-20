from dataclasses import dataclass
from typing import Literal, Optional, Dict, Any
import base64

@dataclass
class Message:
    def __init__(self, origin: str, message: str, image: dict = None):
        self.origin = origin
        self.message = message
        self.image = image  
        