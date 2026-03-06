from pydantic import BaseModel, Field


class ProjectRequest(BaseModel):
    prompt: str = Field(min_length=5)


class ProjectResponse(BaseModel):
    status: str
    message: str
