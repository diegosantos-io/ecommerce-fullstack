from app.services.email_service import send_email


send_email(
    to_email="diegoo.ecommerce@gmail.com",
    subject="Teste - E-commerce Full Stack",
    body="""
Olá!

Este é um e-mail de teste enviado pelo nosso
E-commerce Full Stack usando Python e SMTP.

Integração de e-mail funcionando com sucesso!

Diego Santos
""",
)

print("E-mail enviado com sucesso!")