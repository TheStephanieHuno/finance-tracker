from pydantic import BaseModel


class RegisterUserRequestDto(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class RegisterUserResponseDto(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str

class LoginUserRequestDto(BaseModel):
    email:str
    password:str

    