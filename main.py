import os
import pathlib
from time import sleep
import argparse
from urllib.parse import urlsplit, urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def download_book(book_text, books_path_file):
    with open(books_path_file, "w", encoding="utf-8") as book:
        book.write(book_text)


def check_same_name(book_name, names, index=0):
    if book_name in names:
        book_name = f"{book_name}_{str(index)}"
        check_same_name(book_name, names, index + 1)
    else:
        names.append(book_name)

    return book_name


def get_page(page_url, params=None):
    try:
        response = requests.get(page_url, params)
        check_for_redirect(response)
        response.raise_for_status()
        raise requests.exceptions.ConnectionError()
        return response

    except requests.exceptions.ConnectionError:
        print("нет доступа к сети повторная попытка через 5 секунд")
        sleep(5)
        get_page(page_url, params=None)


def check_for_redirect(response):
    for redirect in response.history:
        if redirect.status_code == 302:
            raise requests.exceptions.HTTPError


def parse_book_page(soup, page_url, names):
    book_image_div = soup.find("div", class_="bookimage")
    book_image_div = book_image_div.find('img')['src']
    photo_url = urljoin(page_url, book_image_div)

    title_tag = soup.find('h1')
    genre = soup.find(class_="d_book")
    book_name, author = title_tag.text.split('   ::   ')
    book_name = sanitize_filename(f'{book_name}_{author}')
    file_name = check_same_name(book_name, names)
    return file_name, photo_url, genre, author


def download_img(path, img):
    with open(path, 'wb') as file:
        file.write(img)


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
    names = []
    for book_id in range(start_id, end_id):
            try:
                params = {
                    "id": book_id,
                }
                book_text_url = urljoin(library_domin, txt_path, )
                book_text_page = get_page(book_text_url, params=params)

                book_text = book_text_page.text

                page_url = f"{library_domin}/b{book_id}"
                book_page = get_page(page_url)
                soup = BeautifulSoup(book_page.text, 'lxml')
                file_name, photo_url, genre, author = parse_book_page(soup, page_url, names)

                books_path_file = os.path.join(books_folder_name, f"{file_name}.txt")

                img = get_page(photo_url).content
                parse = urlsplit(photo_url)
                extension = os.path.splitext(parse.path)[-1]

                img_path_file = os.path.join(image_folder_name, f"{file_name}{extension}")

                download_book(book_text, books_path_file)
                download_img(img_path_file, img)
            except requests.exceptions.HTTPError:
                print("requests.exceptions.HTTPError")



if __name__ == '__main__':
    main()
