from typing import Optional, Union, List
from pydantic import BaseModel

class TranscriptionResponse(BaseModel):
    text: str

class CommandValidationResponse(BaseModel):
    file_id: str
    type: str
    id: List[str]
    name: List[str]
    bank_name: List[str]
    amount: Optional[Union[int, float]] = None
    bill_type: List[str]
    bill_name: List[str]
    mobile_number: List[str]
    statement_period_month: str
    statement_period_year: str
    detected_language: str
    payee_name: str
    payee_bank_name: str
    payee_account_number: str
    card_discount: bool


SUPPORTED_FORMATS = {
    "audio/mpeg", "audio/mp4", "audio/wav", "audio/webm",
    "audio/m4a", "audio/ogg", "audio/flac", "audio/3gpp"
}
