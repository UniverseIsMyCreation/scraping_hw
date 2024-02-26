# обертка над url
# чтобы хранить кол-во попыток для получения контента
class Item:
    def __init__(
        self, url: str, tries: int=0
    ) -> None:
        self.url = url
        self.tries = tries