import logging
import time

from app.database.database import SessionLocal
from app.services.email_outbox_service import (
    process_next_email,
    recover_stale_processing_emails,
)

POLL_INTERVAL_SECONDS = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)




def run_worker() -> None:
    logger.info("Worker de e-mails iniciado.")

    # Tenta recuperar tarefas abandonadas até conseguir.
    while True:
        try:
            with SessionLocal() as db:
                recovered = recover_stale_processing_emails(db)

            logger.info(
                "Recuperação inicial concluída: %s tarefa(s).",
                recovered,
            )
            break

        except KeyboardInterrupt:
            logger.info("Worker de e-mails encerrado.")
            return

        except Exception:
            logger.exception(
                "Falha na recuperação inicial. Tentando novamente em %s segundos.",
                POLL_INTERVAL_SECONDS,
            )
            time.sleep(POLL_INTERVAL_SECONDS)

            if __name__ == "__main__":
                run_worker()

    # Loop principal de processamento.
    while True:
        try:
            with SessionLocal() as db:
                processed = process_next_email(db)

            if not processed:
                time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("Worker de e-mails encerrado.")
            break

        except Exception:
            logger.exception(
                "Erro inesperado no worker. Tentando novamente em %s segundos.",
                POLL_INTERVAL_SECONDS,
            )
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == '__main__':
    run_worker()
