import pathlib
import json

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, urljoin

from main import get_page, book_downloud


def dbg(a):
    print(a)
    exit()


def maker_json(books_properties):
    with open("book_properties.json", "w", encoding='utf8') as file:
        json.dump(books_properties, file, indent=4, ensure_ascii=False)


def main():
    books_folder_name = "books"
    pathlib.Path(books_folder_name).mkdir(parents=True, exist_ok=True)

    image_folder_name = "imge"
    pathlib.Path(image_folder_name).mkdir(parents=True, exist_ok=True)

    library_domin = 'https://tululu.org'

    txt_path = "/txt.php"

    category_id = "55"
    last_page = 2
    books_properties = {}
    for page_id in range(1, last_page):
        try:
            category_url = f"{library_domin}/l{category_id}/{page_id}/"
            category_page = get_page(category_url).text
            soup = BeautifulSoup(category_page, "lxml")

            books_table = soup.select("table.d_book")

            for book in books_table:
                book_id = soup.select("a")[0]["href"][2:-1]
                book_properties = book_downloud(book_id, library_domin, txt_path, books_folder_name, image_folder_name)
                books_properties[book_id] = book_properties
        except requests.exceptions.HTTPError:
            print(f"txt версии книги с id {book_id} нет")

    maker_json(books_properties)


if __name__ == '__main__':
    main()
