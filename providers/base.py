from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
@dataclass
class Reading:
    provider_id: str
    display_name: str
    enabled: bool = True
    source: str = ''
    remaining_value: object = None
    remaining_percent: Optional[float] = None
    unit: str = ''
    reset_at: object = None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = 'OK'
    error_message: str = ''
    window: str = ''
    details: dict = field(default_factory=dict)
