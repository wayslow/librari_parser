class PageDontExist(Exception):
    def __init__(self, *args):
        if args:
            self.page_url = args[0]
        else:
            self.page_url = None

    def __str__(self):
        print('calling str')
        if self.page_url:
            return f'PageDontExist: {self.page_url} страницы нет'
        else:
            return 'PageDontExist: некой страницы нет'