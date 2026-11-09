
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PermissionGrantRequest(BaseModel):
    document_id: UUID
    user_id: UUID

    can_read: bool = False
    can_edit: bool = False
    can_download: bool = False


class PermissionResponse(BaseModel):
    id: str
    document_id: str
    user_id: str

    can_read: bool
    can_edit: bool
    can_download: bool

    is_active: bool

    model_config = ConfigDict(from_attributes=True)
class PermissionCheckResponse(BaseModel):
    document_id: str
    user_id: str

    is_owner: bool = False
    is_admin: bool = False

    can_read: bool = False
    can_edit: bool = False
    can_download: bool = False

    is_active: bool = False