import uuid
from typing import Any

from backend.app.schemas.common import ORMModel


class AsyncTaskResponse(ORMModel):
    id: uuid.UUID
    task_type: str
    status: str
    progress: int
    result: dict[str, Any] | None = None
    error_message: str | None = None

