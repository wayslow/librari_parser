import os
import json
import pathlib
import argparse
from time import sleep
from pprint import pprint
from urllib.parse import urlsplit, urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

LIBRARY_DOMIN = 'https://tululu.org'
TXT_PATH = "/txt.php"


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


def parse_book_page(page_url):
    book_page = get_page(page_url)
    soup = BeautifulSoup(book_page.text, 'lxml')

    book_image_div = soup.select_one("div.bookimage img")['src']
    photo_url = urljoin(page_url, book_image_div)
    genre = soup.select_one("span.d_book a").text

    title = soup.select_one("h1").text

    book_name, author = title.split('   ::   ')
    file_name = sanitize_filename(f'{book_name}_{author}')

    comments_tags = soup.select("div.texts")

    coments = []
    for comments_tag in comments_tags:
        coments.append(comments_tag.select_one("span").text)
    book_properties = {
        "file_name": file_name,
        "photo_url": photo_url,
        "author": author,
        "coments": coments,
        "genre": genre,
    }

    return book_properties


def image_downloud(book_properties, image_folder_name, file_name):
    photo_url = book_properties["photo_url"]
    img = get_page(photo_url).content
    parse = urlsplit(photo_url)
    extension = os.path.splitext(parse.path)[-1]
    img_path_file = os.path.join(image_folder_name, f"{file_name}{extension}")
    book_properties["img_path"] = img_path_file
    with open(img_path_file, 'wb') as file:
        file.write(img)

    return book_properties


def book_downloud(book_id, books_folder_name, book_properties, file_name):
    params = {
        "id": book_id,
    }
    book_text_url = urljoin(LIBRARY_DOMIN, TXT_PATH)
    book_text_page = get_page(book_text_url, params=params)

    book_text = book_text_page.text

    books_path_file = os.path.join(books_folder_name, f"{file_name}_{book_id}.txt")
    book_properties["books_path"] = books_path_file
    with open(books_path_file, "w", encoding="utf-8") as book:
        book.write(book_text)

    return book_properties


def maker_json(books_properties, file_path):
    with open(file_path, encoding='utf8') as file:
        in_file_properties = json.load(file)

    books_properties = books_properties | in_file_properties

    with open(file_path, 'w', encoding='utf8') as file:
        json.dump(books_properties, file, indent=4, ensure_ascii=False)


def find_end_id(category_url):
    category_page = get_page(category_url).text
    soup = BeautifulSoup(category_page, "lxml")
    end_id = soup.select("a.npage")[-1].text
    return int(end_id)


def catrgory_pars(category_url, books_folder_name, image_folder_name, skip_txt, skip_img, json_file_path):
    books_properties = {}
    try:
        category_page = get_page(category_url).text

        soup = BeautifulSoup(category_page, "lxml")

        books_table = soup.select("table.d_book")

        for book in books_table:
            book_id = book.select("a")[0]["href"][2:-1]
            page_url = f"{LIBRARY_DOMIN}/b{book_id}/"
            book_properties = parse_book_page(page_url)
            file_name = book_properties["file_name"]
            if skip_txt:
                book_properties = book_downloud(book_id, books_folder_name, book_properties, file_name)
            if skip_img:
                book_properties = image_downloud(book_properties, image_folder_name, file_name)

            books_properties[book_id] = book_properties
    except requests.exceptions.HTTPError:
        print("requests.exceptions.HTTPError")
    finally:
        maker_json(books_properties, json_file_path)


def main():
    parser = argparse.ArgumentParser(description="скачивает книги по id с онлайн библиотеки tululu.org")
    parser.add_argument('--start_page', help='начальное страницы id', default=1, type=int)
    parser.add_argument('--end_page', help='конечное страницы id', default=None, type=int)
    parser.add_argument('--category_id', help='id котегории', default=55, type=int)
    parser.add_argument('--dest_folder', help='путь к папке сохранеия', default="", type=str)
    parser.add_argument('--skip_img', help=' сохранять изображение', action="store_true")
    parser.add_argument('--skip_txt', help=' сохранять текст', action="store_true")

    args = parser.parse_args()
    start_id = args.start_page
    end_id = args.end_page
    category_id = args.category_id
    dest_folder = args.dest_folder
    skip_img = args.skip_img
    skip_txt = args.skip_txt

    print(skip_img, skip_txt)

    books_folder_name = "books"
    if not skip_txt:
        books_folder_name = os.path.join(dest_folder, books_folder_name)
        pathlib.Path(books_folder_name).mkdir(parents=True, exist_ok=True)

    image_folder_name = "imge"
    if not skip_img:
        image_folder_name = books_folder_name = os.path.join(dest_folder, image_folder_name)
        pathlib.Path(image_folder_name).mkdir(parents=True, exist_ok=True)

    pathlib.Path(dest_folder).mkdir(parents=True, exist_ok=True)

    json_file_path = os.path.join(dest_folder, "book_properties.json")

    category_url = f"{LIBRARY_DOMIN}/l{category_id}/"

    if not end_id:
        end_id = find_end_id(category_url)

    for page_id in range(start_id, end_id):
        category_page_url = f"{category_url}{page_id}/"

        catrgory_pars(category_page_url, books_folder_name, image_folder_name, skip_txt, skip_img, json_file_path)


if __name__ == '__main__':
    main()
