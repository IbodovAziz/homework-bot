import os
import time
import logging
import sys

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exeptions import (
    TokenError, SendMessageError, UnavailabilityError, APIError, ResponseError,
    NameHomeworkError, EmptyStatus, UndocumentedStatus
)

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = 861489716

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка токенов."""
    if all(
            [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    ):
        logger.info('Проверка токенов прошла успешна!')
        return True
    logger.critical('Ошибка в переменных окружения!')
    raise TokenError('Невалидный токен!')


def send_message(bot: TeleBot, message: str):
    """Отправка сообщения через бота."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        # print('Успешно отправлено сообщение в Telegram')
        logger.debug(f'Успешно отправлено сообщение в Telegram: "{message}"')
    except SendMessageError as er:
        msg = f'сбой при отправке сообщения в Telegram {er}'
        logger.error(msg)
        raise SendMessageError


def get_api_answer(timestamp: int):
    """Запрос на API, проверка на валидность."""
    from_date = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=from_date)
        if response.status_code != 200:
            raise UnavailabilityError('API unavailability')
    except requests.exceptions.RequestException as er:
        msg = f'сбои при запросе к эндпоинту : {er}'
        logger.error(msg)
        raise APIError(msg)
    else:
        return response.json()


def check_response(response):
    """Проверка ответа от API."""
    if not isinstance(response, dict):
        logger.error('Тип данных не соответствует.')
        raise TypeError
    if 'homeworks' not in response:
        msg = 'отсутствие ожидаемых ключей в ответе API.'
        logger.error(msg)
        raise ResponseError(msg)
    if not isinstance(response['homeworks'], list):
        logger.error('под ключом `homeworks` данные не в виде списка.')
        raise TypeError

    return response


def parse_status(homework):
    """Обработка словаря с данными."""

    homework_name = homework.get('homework_name')
    if not homework_name:
        msg = f'Ключ {homework_name} отсутствует.'
        logger.error(msg)
        raise NameHomeworkError(msg)

    status = homework.get('status')
    if not status:
        msg = f'Ошибка в статусе: {status}.'
        logger.error(msg)
        raise EmptyStatus(msg)

    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        msg = f'Получен недокументированный статус домашней работы: {status}'
        logger.error(msg)
        raise UndocumentedStatus(msg)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)

    timestamp = int(time.time())
    cur_status = None

    while True:
        try:
            response = get_api_answer(timestamp)
            data = check_response(response)

            if not data.get('homeworks'):
                logger.debug('Отсутствуют обновления.')
            else:
                homework = data['homeworks'][0]
                if homework:
                    status = homework['status']
                    if status != cur_status:
                        send_message(bot, parse_status(homework))
                        cur_status = status
                    else:
                        timestamp = response.get('current_date', timestamp)
                        logger.debug('Отсутсвует обновление статуса.')
                        send_message(bot, 'Статус не изменился, проверяем дальше')
        except Exception as error:
            logger.error(error)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
