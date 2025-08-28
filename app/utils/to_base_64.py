import base64
from typing import Optional

def to_base64(data: Optional[bytes]) -> Optional[str]:
    if data is None:
        return None
    return base64.b64encode(data).decode("utf-8")