import os
import json
import pathlib
import argparse
from time import sleep
from urllib.parse import urlsplit, urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

from catom_exsepsions import PageDontExist
from parse_tululu import get_page

LIBRARY_DOMAIN = 'https://tululu.org'
TXT_PATH = "/txt.php"


def get_book_properties(soup, page_url, skip_txt, skip_img, books_folder_name, image_folder_name, book_id):
    book_image_div = soup.select_one("div.bookimage img")['src']

    photo_url = urljoin(page_url, book_image_div)
    genre = soup.select_one("span.d_book a").text

    title = soup.select_one("h1").text

    book_name, author = title.split('   ::   ')
    file_name = sanitize_filename(f'{book_name}_{author}')

    comments_tags = soup.select("div.texts")

    comments = [comments_tag.select_one("span").text for comments_tag in comments_tags]

    book_properties = {
        "file_name": file_name,
        "photo_url": photo_url,
        "author": author,
        "comments": comments,
        "genre": genre,
    }

    if not skip_txt:
        books_path_file = os.path.join(books_folder_name, f"{file_name}_{book_id}.txt")
        book_properties["books_path"] = books_path_file

    if not skip_img:
        photo_url = book_properties["photo_url"]
        parse = urlsplit(photo_url)
        extension = os.path.splitext(parse.path)[-1]
        img_path_file = os.path.join(image_folder_name, f"{file_name}{extension}")
        book_properties["img_path"] = img_path_file

    return book_properties


def image_download(photo_url, img_path_file):
    img = get_page(photo_url).content
    with open(img_path_file, 'wb') as file:
        file.write(img)


def book_download(book_id, books_path_file, ):
    params = {
        "id": book_id,
    }
    book_text_url = urljoin(LIBRARY_DOMAIN, TXT_PATH)
    book_text_page = get_page(book_text_url, params=params)

    book_text = book_text_page.text

    with open(books_path_file, "w", encoding="utf-8") as book:
        book.write(book_text)


def make_json(books_properties, json_file_path):
    with open(json_file_path, 'w', encoding="utf-8") as file:
        json.dump(books_properties, file, indent=4, ensure_ascii=False)


def find_end_id(category_url):
    category_page = get_page(category_url).text
    soup = BeautifulSoup(category_page, "lxml")
    end_id = soup.select("a.npage")[-1].text
    return int(end_id)


def parse_category(category_page_url, books_folder_name, image_folder_name, skip_txt, skip_img, books_properties):
    category_page = get_page(category_page_url).text
    soup = BeautifulSoup(category_page, "lxml")
    books_table = soup.select("table.d_book")

    for book in books_table:
        book_id = book.select_one("a")["href"][2:-1]

        page_url = f"{LIBRARY_DOMAIN}/b{book_id}/"
        book_page = get_page(page_url)
        soup = BeautifulSoup(book_page.text, 'lxml')

        book_properties = get_book_properties(soup, page_url)

        get_book_properties(soup, page_url, skip_txt, skip_img, books_folder_name, image_folder_name, book_id)

        books_properties[*book_id] = book_properties
    return books_properties


def main():
    parser = argparse.ArgumentParser(description="скачивает книги по id с онлайн библиотеки tululu.org")
    parser.add_argument('--start_page', help='начальное id страницы', default=1, type=int)
    parser.add_argument('--end_page', help='конечное id страницы', default=None, type=int)
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

    books_folder_name = "books"
    if not skip_txt:
        books_folder_name = os.path.join(dest_folder, books_folder_name)
        pathlib.Path(books_folder_name).mkdir(parents=True, exist_ok=True)

    image_folder_name = "imge"
    if not skip_img:
        image_folder_name = os.path.join(dest_folder, image_folder_name)
        pathlib.Path(image_folder_name).mkdir(parents=True, exist_ok=True)

    pathlib.Path(dest_folder).mkdir(parents=True, exist_ok=True)
    json_file_path = os.path.join(dest_folder, "book_properties.json")

    pathlib.Path(json_file_path).unlink(missing_ok=True)

    category_url = f"{LIBRARY_DOMAIN}/l{category_id}/"
    books_properties = {}
    try:
        if not end_id:
            end_id = find_end_id(category_url)
        for page_id in range(start_id, end_id):
            category_page_url = f"{category_url}{page_id}/"
            books_properties = parse_category(category_page_url, books_folder_name, image_folder_name,
                                              skip_txt,skip_img, books_properties)
    except requests.exceptions.HTTPError:
        print("requests.exceptions.HTTPError")
    except requests.exceptions.ConnectionError:
        print("requests.exceptions.ConnectionError")
        sleep(5)
    except PageDontExist as ex:
        print(ex)
    finally:
        make_json(books_properties, json_file_path)


if __name__ == '__main__':
    main()
