
import threading
import time

from sqlalchemy import text

from app.database.database import engine


def test_postgres_for_update_bloqueia_segunda_sessao():
    """
    Verifica se SELECT FOR UPDATE faz uma segunda sessão
    aguardar enquanto a primeira mantém o bloqueio.
    """
    lock_adquirido = threading.Event()
    segunda_sessao_iniciou = threading.Event()
    segunda_sessao_concluiu = threading.Event()
    erros = []

    with engine.connect() as conexao:
        conexao.execute(text("BEGIN"))
        conexao.execute(text("SELECT pg_advisory_xact_lock(987654321)"))

        def segunda_sessao():
            try:
                with engine.connect() as outra_conexao:
                    outra_conexao.execute(text("BEGIN"))
                    segunda_sessao_iniciou.set()

                    outra_conexao.execute(
                        text("SELECT pg_advisory_xact_lock(987654321)")
                    )

                    segunda_sessao_concluiu.set()
                    outra_conexao.execute(text("ROLLBACK"))
            except Exception as erro:
                erros.append(erro)

        thread = threading.Thread(target=segunda_sessao)
        thread.start()

        try:
            assert segunda_sessao_iniciou.wait(timeout=5)

            # Dá tempo para a segunda sessão tentar adquirir o bloqueio.
            time.sleep(0.5)
            assert not segunda_sessao_concluiu.is_set()

        finally:
            conexao.execute(text("ROLLBACK"))

        thread.join(timeout=5)

    assert not thread.is_alive(), "A segunda sessão ficou bloqueada."
    assert not erros, f"Erro na segunda sessão: {erros}"
    assert segunda_sessao_concluiu.is_set()


import threading

import pytest
from sqlalchemy import text

from app.database.database import engine


def test_postgres_for_update_bloqueia_mesmo_pedido():
    segunda_sessao_iniciou = threading.Event()
    segunda_sessao_obteve_bloqueio = threading.Event()
    erros = []

    with engine.connect() as primeira:
        transacao = primeira.begin()

        try:
            order_id = primeira.execute(
                text("SELECT id FROM orders ORDER BY id LIMIT 1 FOR UPDATE")
            ).scalar_one_or_none()

            if order_id is None:
                pytest.skip("Não há pedidos para testar o bloqueio real.")

            def tentar_bloquear_pedido():
                try:
                    with engine.connect() as segunda:
                        with segunda.begin():
                            segunda_sessao_iniciou.set()

                            segunda.execute(
                                text(
                                    "SELECT id FROM orders "
                                    "WHERE id = :order_id FOR UPDATE"
                                ),
                                {"order_id": order_id},
                            )

                            segunda_sessao_obteve_bloqueio.set()
                except Exception as erro:
                    erros.append(erro)

            thread = threading.Thread(target=tentar_bloquear_pedido)
            thread.start()

            assert segunda_sessao_iniciou.wait(timeout=5)

            # A primeira sessão ainda mantém o bloqueio.
            assert not segunda_sessao_obteve_bloqueio.wait(timeout=0.5)

        finally:
            transacao.rollback()

        thread.join(timeout=5)

    assert not thread.is_alive(), "A segunda sessão não terminou."
    assert not erros, f"Erro na segunda sessão: {erros}"
    assert segunda_sessao_obteve_bloqueio.is_set()
