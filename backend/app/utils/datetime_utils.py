from datetime import UTC, datetime


def utc_now_naive() -> datetime:
    """Retorna a data/hora UTC sem informação de fuso, compatível com DateTime."""
    return datetime.now(UTC).replace(tzinfo=None)
