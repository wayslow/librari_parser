import os
import pathlib
from time import sleep
import argparse
from urllib.parse import urlsplit, urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def get_page(page_url, params=None):
    while True:
        try:
            response = requests.get(page_url, params)
            check_for_redirect(response)
            response.raise_for_status()
            return response
            break
        except requests.exceptions.ConnectionError:
            print("нет доступа к сети повторная попытка через 5 секунд")
            sleep(5)


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def parse_book_page(soup, page_url):
    book_image_div = soup.select("div.bookimage img")[0]['src']
    photo_url = urljoin(page_url, book_image_div)
    genre = soup.select("span.d_book a")[0].text

    title = soup.select("h1")[0].text

    book_name, author = title.split('   ::   ')
    file_name = sanitize_filename(f'{book_name}_{author}')

    comments_tags = soup.select("div.texts")

    coments = []
    for comments_tag in comments_tags:
        coments.append(comments_tag.find("span").text)
    book_properties = {
        "file_name": file_name,
        "photo_url": photo_url,
        "author": author,
        "coments": coments,
        "genre": genre,
    }

    return book_properties


def book_downloud(book_id, library_domin, txt_path, books_folder_name, image_folder_name):
    params = {
        "id": book_id,
    }
    book_text_url = urljoin(library_domin, txt_path)
    book_text_page = get_page(book_text_url, params=params)

    book_text = book_text_page.text
    page_url = f"{library_domin}/b{book_id}/"
    book_page = get_page(page_url)
    soup = BeautifulSoup(book_page.text, 'lxml')
    book_properties = parse_book_page(soup, page_url)
    file_name = book_properties["file_name"]
    photo_url = book_properties["photo_url"]

    books_path_file = os.path.join(books_folder_name, f"{file_name}_{book_id}.txt")

    img = get_page(photo_url).content
    parse = urlsplit(photo_url)
    extension = os.path.splitext(parse.path)[-1]
    img_path_file = os.path.join(image_folder_name, f"{file_name}{extension}")
    book_properties["img_path"] = img_path_file
    book_properties["books_path"] = books_path_file
    with open(books_path_file, "w", encoding="utf-8") as book:
        book.write(book_text)

    with open(img_path_file, 'wb') as file:
        file.write(img)
    return book_properties


def main():
    parser = argparse.ArgumentParser(description="скачивает книги по id с онлайн библиотеки tululu.org")
    parser.add_argument('--start_page', help='начальное id', default=1, type=int)
    parser.add_argument('--end_page', help='конечное id', default=3, type=int)
    args = parser.parse_args()
    start_id = args.start_page
    end_id = args.end_page

    books_folder_name = "books"
    pathlib.Path(books_folder_name).mkdir(parents=True, exist_ok=True)

    image_folder_name = "imge"
    pathlib.Path(image_folder_name).mkdir(parents=True, exist_ok=True)

    library_domin = 'https://tululu.org'
    txt_path = "/txt.php"
    for book_id in range(start_id, end_id):
        try:
            book_downloud(book_id, library_domin, txt_path, books_folder_name, image_folder_name)
        except requests.exceptions.HTTPError:
            print("requests.exceptions.HTTPError")


if __name__ == '__main__':
    main()
