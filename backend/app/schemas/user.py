from pydantic import BaseModel, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, senha: str) -> str:
        if not any(letra.isupper() for letra in senha):
            raise ValueError(
                "A senha deve conter pelo menos uma letra maiúscula."
            )

        if not any(not caractere.isalnum() for caractere in senha):
            raise ValueError(
                "A senha deve conter pelo menos um caractere especial."
            )

        return senha

class UserResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    role: str
    ativo: bool

    model_config = {
        "from_attributes": True
    }

class UserLogin(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str