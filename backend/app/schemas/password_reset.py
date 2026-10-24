from pydantic import BaseModel, EmailStr, Field, field_validator


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    nova_senha: str = Field(min_length=8, max_length=128)

    @field_validator("nova_senha")
    @classmethod
    def validar_nova_senha(cls, senha: str) -> str:
        if not any(letra.isupper() for letra in senha):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
        if not any(not caractere.isalnum() for caractere in senha):
            raise ValueError("A senha deve conter pelo menos um caractere especial.")
        return senha


class PasswordResetMessage(BaseModel):
    message: str
