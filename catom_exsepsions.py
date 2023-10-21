class PageDontExist(Exception):
    def __init__(self, *args):
        if args:
            self.page_url = args[0]
            self.params = args[1]
        else:
            self.page_url = None

    def __str__(self):
        if self.page_url:
            return f'PageDontExist: страницы: {self.page_url}  и параметрами {self.params}  нет'
        else:
            return 'PageDontExist: некой страницы нет'