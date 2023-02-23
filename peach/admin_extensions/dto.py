from dataclasses import dataclass, field
from typing import Optional, Type, List, Union


@dataclass
class PermissionLimitDTO:
    user_id: Optional[int] = None
    permission_code: Optional[str] = None
    limit_confs: Optional[List] = None
    cleaned_data: Union[dict, Type] = None
    history_data: Optional[dict] = field(default_factory=dict)
