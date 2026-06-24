from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    success: bool = False
    message: str


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
