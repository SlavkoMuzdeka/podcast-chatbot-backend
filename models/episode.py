from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Episode:
    id: str
    title: str
    url: str
    transcript: str
    summary: str
    duration: Optional[int] = None
    created_at: Optional[datetime] = None
    processed: bool = False


@dataclass
class Expert:
    id: str
    name: str
    description: str
    episodes: List[Episode]
    created_at: datetime
    updated_at: datetime
    user_id: str
    namespace: str
