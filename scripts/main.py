import argparse
import os
import sys
module_path = os.path.abspath('..')
if module_path not in sys.path:
    sys.path.append(module_path)
module_path = os.path.abspath('.')
if module_path not in sys.path:
    sys.path.append(module_path)
module_path = os.path.abspath('./runners')
if module_path not in sys.path:
    sys.path.append(module_path)

from parsers.selector import CssSelectorParser
from utils.file_sink import FileSink
from runners.runner import SimpleRunner


def main(url: str, file: str) -> None:
    parser = CssSelectorParser()
    file_sink = FileSink(file)
    runner = SimpleRunner(
        parser=parser, sink=file_sink,
        seed_urls=[url]
    )
    runner.run()


if __name__ == '__main__':
    # создать парсер аргументов
    parser = argparse.ArgumentParser()
    # добавить аргументы
    parser.add_argument('--url', type=str, help='url wikipage')
    parser.add_argument('--file', type=str, help='file для результата')
    # разобрать аргументы
    args = parser.parse_args()
    main(args.url, args.file)