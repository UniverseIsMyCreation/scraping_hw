import json
from runners.utils_run import Item


class FileSink:
    def __init__(self, path: str) -> None:
        # файл для записи
        self._file = open(path, 'w')

    def write(self, item: Item) -> None:
        # дамп результата
        self._file.write(json.dumps(item, ensure_ascii=False) + '\n')

    def __del__(self) -> None:
        # закрытие файла
        self._file.close()