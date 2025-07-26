class TokenError(Exception):
    """Отсутствие или ошибка токена."""


class APIError(Exception):
    """API вернул ошибку."""


class ResponseError(Exception):
    """В ответе API отсутсвует необходимый ключ."""


class SendMessageError(Exception):
    """Ошибка отправки сообщения."""


class UnavailabilityError(Exception):
    """API unavailability, статус != 200"""


class NameHomeworkError(Exception):
    """Ключ NameHomework отсутсвует."""


class EmptyStatus(Exception):
    """Значение ключа статуса пустой."""


class UndocumentedStatus(Exception):
    """Недокументированный статус."""
