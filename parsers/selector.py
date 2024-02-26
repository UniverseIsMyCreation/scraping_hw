from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import re
from typing import (Any, Tuple, List, Dict)


class CssSelectorParser:
    def __init__(self) -> None:
        self.required_columns_team1 = [
            'позиция', 'игрок',
            'дата рождения / возраст', 'матчи',
            'голы', 'клуб'
        ]
        self.required_columns_team2 = [
            'позиция', 'игрок',
            'дата рождения / возраст', 'игры',
            'голы', 'клуб'
        ]
        self.position_decrypted = {
            'Вр': 'вратарь',
            'Нап': 'нападающий',
            'ПЗ': 'полузащитник',
            'Защ': 'защитник'    
        }
        self.date_to_num = {
            'января': '01',
            'февраля': '02',
            'марта': '03',
            'апреля': '04',
            'мая': '05',
            'июня': '06',
            'июля': '07',
            'августа': '08',
            'сентября': '09',
            'октября': '10',
            'ноября': '11',
            'декабря': '12'
        }


    def _check_table(self, table: Any) -> bool:
        # извлечение имен колонок таблицы
        headers = [header.text for header in table.find_all('th')][1:]
        headers = list(filter(lambda x: x != '\n', headers))
        headers = list(map(lambda x: x.replace('\n', '').lower(), headers))
        # проверка кол-ва колонок
        if len(headers) != len(self.required_columns_team1):
            return False
        # проверка имен колонок
        if all(col in headers for col in self.required_columns_team1):
            return True
        if all(col in headers for col in self.required_columns_team2):
            return True
        return False


    def _parse_main_wikipage(
        self, soup: BeautifulSoup, baseurl: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        # css запрос для извлечения ссылок на команды
        countries_links_req = 'table.standard.sortable tbody tr td:has(span) > a'
        # извлечение ссылок
        countries_links = soup.select(countries_links_req)
        # функция для соединения путей в абсолютный
        concat_urls = lambda x: urljoin(baseurl, x)
        extract_relative_urls = lambda x: x.attrs['href']
        # создание абсолютынх путей
        countries_links = list(map(extract_relative_urls, countries_links))
        countries_links_full = list(map(concat_urls, countries_links))
        # возвращение ссылок
        return list(), countries_links_full


    def _parse_one_row_table(
        self, row, baseurl: str, team_name: str
    ) -> Dict[str, Any]:
        result = dict()
        # извлечения атрибутов игрока
        all_attrs = row.find_all('td')[1:]
        # позиция
        position = all_attrs[0].find('a').text.replace('\n', '')
        position_decrypted = self.position_decrypted[position]
        # относительный url
        url_player = all_attrs[1].find('a')['href']
        # timestamp дня рождения
        birth = all_attrs[2].find_all('a')
        day, month = birth[0].text.replace('\n', '').split(' ')
        year = birth[1].text.replace('\n', '')
        datetime_format = year + '-' + self.date_to_num[month] + '-' + day
        birthday_datetime = datetime.strptime(datetime_format, "%Y-%m-%d")
        timestamp = int(birthday_datetime.timestamp())
        # статистика
        national_games = int(all_attrs[3].text.replace('\n', '').replace('−', '-'))
        national_stat = int(all_attrs[4].text.replace('\n', '').replace('−', '-'))
        if position_decrypted in ['вратарь']:
            national_scored = 0
            national_conceded = national_stat
        else:
            national_scored = national_stat
            national_conceded = 0
        # клуб
        club = all_attrs[5].find('a', recursive=False).text.replace('\n', '')
        # сохранение результатов
        full_url_player = urljoin(baseurl, url_player)
        result['url'] = full_url_player
        result['name'] = None
        result['position'] = position_decrypted
        result['current_club'] = club
        result['national_team'] = team_name
        result['birthday'] = timestamp
        result['national_caps'] = national_games
        result['national_scored'] = national_scored
        result['national_conceded'] = national_conceded
        result['height'] = None
        result['club_caps'] = None
        result['club_scored'] = None
        result['club_conceded'] = None
        result['first_part'] = True

        return result, full_url_player


    def _parse_table(
        self, table: Any, baseurl: str, team_name: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        has_a_tag_inside = lambda x: \
            x.name == 'tr' and \
            x.find('td') is not None and \
            x.find('a') is not None
        # извлечение всех нужных строчек с правильным тэгами
        rows = table.find_all(has_a_tag_inside)
        # для хранения иформации об игроках и ссылках на профили
        result_players, next_urls = list(), list()
        for row in rows:
            # информция об игроках из таблицы
            result_player, next_urls_player = self._parse_one_row_table(
                row, baseurl, team_name
            )
            # сохранение
            next_urls.append(next_urls_player)
            result_players.append(result_player)

        return result_players, next_urls


    def _parse_player(
        self, soup, url: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        result_player = dict()
        # имя и фамилия
        player_name = soup.select_one('th.infobox-above div.label')
        try:
            name, surname = player_name.text.replace('\n', '').split(' ')
        except:
            full_name = player_name.text.replace('\n', '').split(' ')
            name, surname = full_name[0], ' '.join(full_name[1:])
        # ищем рост
        results = soup.select('table.infobox td.plainlist span.no-wikidata')
        height = None
        for result in results:
            try:
                nums = re.findall(r'\d+', result.text)
                nums = list(filter(lambda x: len(x)==3, nums))
                height = int(nums[0])
                break
            except:
                pass
        # ищем показатели в клубах
        results = soup.select('td.infobox-table tr')
        # флаг отслеживания статистики или нет
        flag_search = False
        # паттерн для поиска статистики
        stat_pattern = r'([+-−−]?\d+)'
        all_games, all_stat = 0, 0
        for result in results:
            col_name = result.find('th')
            # сохранение информации при проходе по клубам
            if col_name is not None:
                if re.search(r'Клубная карьера', col_name.text):
                    flag_search = True
                else:
                    flag_search = False
            if col_name is None and flag_search:
                # извлечение статистики по клубу
                nums = re.findall(stat_pattern, result.find_all('td')[-1].text)
                games, stat = nums
                # обрабаботка
                stat = int(stat.replace('–', '-').replace('−', '-').replace('\n', ''))
                games = int(games.replace('\n', ''))
                # суммирование
                all_games += games
                all_stat += stat
        # сохранение статистики
        result_player['url'] = url
        result_player['name'] = [surname, name]
        result_player['stat'] = all_stat
        result_player['club_caps'] = all_games
        result_player['height'] = height
        result_player['first_part'] = False

        return [result_player], list()


    def parse(
        self, content: Any, cur_page_url: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        # парсинг контента сайта
        soup = BeautifulSoup(content, 'html.parser')
        result = soup.select_one('div.footballbox')
        if result is not None:
            # парсинг главной страницы
            content_page, next_urls = self._parse_main_wikipage(
                soup, cur_page_url
            )
            return content_page, next_urls
        # извлечение всех таблиц
        tables = soup.select('table.wikitable')
        final_table = None
        for table in tables:
            # проверка таблицы с игроками
            if self._check_table(table):
                final_table = table
                break
        # в случае нахождение таблицы с игроками
        if final_table is not None:
            # парсинг таблицы с игроками страны
            team_name = soup.select_one('span.mw-page-title-main').text
            content_page, next_urls = self._parse_table(
                table, cur_page_url, team_name
            )
            return content_page, next_urls
        # находимся на странице с игроком
        content_page, next_urls = self._parse_player(soup, cur_page_url)
        return content_page, next_urls