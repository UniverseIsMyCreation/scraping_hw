from collections import deque
import requests
from typing import (List, Tuple, Any)

from utils_run import Item
from parsers.selector import CssSelectorParser
from utils.file_sink import FileSink


class SimpleRunner:
    def __init__(
        self, parser: CssSelectorParser, sink: FileSink,
        seed_urls: List[str], max_tries: int=5, logging: bool=False
    ) -> None:
        # коллекция игроков
        self._collection = dict()
        # парсер сайта
        self._parser = parser
        # логгирование итогового результата в файл
        self._sink = sink
        # множество просмотренных url
        self._seen = set()
        # очередь url на обработку
        self._to_process = deque()
        for elem in seed_urls:
            self._submit(Item(elem))
        # макс кол-во попыток на получение контента
        self._max_tries = max_tries
        # логирование в консоль
        self.logging = logging


    def _download(self, item: Item) -> Tuple[Any, List[str]]:
        # извлечение содержимого по url
        resp = requests.get(item.url, timeout=60)
        # raise в случае ошибки
        # извлечение контента иначе
        resp.raise_for_status()
        # извлечение контента
        content = resp.content
        # извлечение контента сайта и его ссылок
        return self._parser.parse(content, resp.url)


    def _submit(self, item: Item) -> None:
        # добавление в очередь на обработку url
        self._to_process.append(item)
        # добавление в множество просмотренных url
        self._seen.add(item.url)


    def run(self) -> None:
        # пока есть url на обработку
        while self._to_process:
            # достаем url
            item = self._to_process.popleft()
            result, next = self._download(item)
            try:
                # извлечение контента и ссылок на другие сайты
                pass
            except Exception as e:
                # увелечение кол-ва попыток на чтение запроса
                item.tries += 1
                if item.tries >= self._max_tries:
                    # в случае превыщения кол-ва попыток дамп ошибки
                    self._write(item, error=str(e), logging=self.logging)
                continue
            # если контент не пустой
            if result:
                for elem in result:
                    if elem['first_part']:
                        # первая часть профиля игрока из таблицы
                        url_key = elem['url']
                        self._collection[url_key] = elem
                    else:
                        # вторая часть профиля игрока из таблицы
                        url_key = elem['url']
                        player_card = self._collection[url_key]
                        for key, val in elem.items():
                            if player_card.get(key, None) is None:
                                player_card[key] = val
                        # обновление статистики по клубу
                        if player_card['position'] in ['вратарь']:
                            player_card['club_scored'] = 0
                            player_card['club_conceded'] = player_card['stat']
                        else:
                            player_card['club_scored'] = player_card['stat']
                            player_card['club_conceded'] = 0
                        # удаление лишних полей
                        del player_card['stat']
                        del player_card['first_part']
                        del self._collection[url_key]
                        self._write(item, result=player_card, logging=self.logging)
            # проход по всем ссылкам
            for elem in next:
                # если такая ссылка уже была
                if elem in self._seen:
                    continue
                # иначе добавление в очередь на обработку
                self._submit(Item(elem))


    def _write(
        self, item: Item, result: Any=None,
        error: Exception=None, logging: bool=False
    ) -> None:
        # в случае отсутствия результата или ошибки
        if result is None and error is None:
            raise RuntimeError('Invalid result. Both result and error are None')
        # конвертация формата полученных данных
        if logging and result is not None:
            print(result)
        if logging and error is not None:
            print(error)
        to_write = {'tries': item.tries, 'result': result, 'error': error}
        # запись в файл
        self._sink.write(to_write)