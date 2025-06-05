from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel


class AccessCodeBase(BaseModel):
    code: str
    is_used: bool = False
    created_at: datetime
    used_at: Optional[datetime] = None
    used_by: Optional[str] = None
    usage_data: Optional[Dict] = None
    full_name: Optional[str] = None
    squad_number: Optional[int] = None
    shift_number: Optional[int] = None

class AccessCodeCreate(AccessCodeBase):
    pass

class AccessCodeUpdate(BaseModel):
    is_used: Optional[bool] = None
    used_at: Optional[datetime] = None
    used_by: Optional[str] = None
    usage_data: Optional[Dict] = None
    full_name: Optional[str] = None
    squad_number: Optional[str] = None
    shift_number: Optional[str] = None

class AccessCodeInDB(AccessCodeBase):
    id: int
    created_by_id: int

    class Config:
        from_attributes = True

class AccessCodeResponse(AccessCodeInDB):
    pass

class AccessCodeList(BaseModel):
    items: list[AccessCodeResponse]
    total: int
    skip: int
    limit: int

class AccessCodeUsage(BaseModel):
    full_name: str
    squad_number: int
    shift_number: int

class FormData(BaseModel):
    name: str
    surname: str
    shift: str
    group: str
    promocode: str
    agree: bool

class SquadPromocodes(BaseModel):
    squad_number: int
    promocodes: List[AccessCodeResponse]

class ShiftPromocodesResponse(BaseModel):
    shift_number: int
    squads: List[SquadPromocodes]
