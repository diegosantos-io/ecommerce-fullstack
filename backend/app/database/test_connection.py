from sqlalchemy import text

from app.database.database import engine


try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("Conexão com PostgreSQL realizada com sucesso!")


except Exception as error:
    print(f"Erro ao conectar com PostgreSQL: {error}")

    