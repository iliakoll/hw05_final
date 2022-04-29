from datetime import date


def year(request: str) -> int:
    """Добавляет переменную с текущим годом."""
    dt = date.today()
    return {
        'year': dt.year
    }
