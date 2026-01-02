from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class lists:
    incident_id: Optional[str]
    service: Optional[str]
    status: Optional[str]
    detail: str
    occurred_at: Optional[str]
    restored_at: Optional[str]
    logs: List[Any]

    def get_id(self):
        return self.incident_id

    def get_service(self):
        return self.service

    def get_status(self):
        return self.status

    def get_detail(self):
        return self.detail

    def get_occurred_at(self):
        return self.occurred_at

    def get_restored_at(self):
        return self.restored_at

    def get_logs(self):
        return self.logs
