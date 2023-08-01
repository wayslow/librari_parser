import os
import pathlib
from itertools import count
import argparse
from urllib.parse import urlsplit, urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

names_list = []


def download_book(book_text, books_path_file):
    with open(books_path_file, "w", encoding="utf-8") as book:
        book.write(book_text)


def check_same_name(book_name):
    verifiable_book_name = book_name

    for index in count(1):
        if verifiable_book_name in names_list:
            verifiable_book_name = f"{book_name}_{str(index)}"
        else:
            names_list.append(verifiable_book_name)
            break

    return verifiable_book_name


def get_page(page_url, params=None):
    response = requests.get(page_url, params)
    response.raise_for_status()
    return response


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def get_book_characteristic(soup, page_url):
    book_image_div = soup.find("div", class_="bookimage")
    book_image_div = book_image_div.find('img')['src']
    photo_url = urljoin(page_url, book_image_div)

    title_tag = soup.find('h1')
    book_name = sanitize_filename("_".join(title_tag.text.split('   ::   ')[0].split(" ")).strip())
    file_name = check_same_name(book_name)
    return file_name, photo_url


def download_img(path, img):
    with open(path, 'wb') as file:
        file.write(img)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', help='начальное id', default=1)
    parser.add_argument('--end_page', help='конечное id', default=3)
    args = parser.parse_args()
    start_id = int(args.start_page)
    end_id = int(args.end_page)

    books_folder_name = "books"
    pathlib.Path(books_folder_name).mkdir(parents=True, exist_ok=True)

    image_folder_name = "imge"
    pathlib.Path(image_folder_name).mkdir(parents=True, exist_ok=True)
    domin = 'https://tululu.org'
    txt_path = "/txt.php"
    for book_id in range(start_id, end_id):
        try:
            params = {
                "id": book_id,
            }
            book_text_url = urljoin(domin, txt_path)
            book_text_page = get_page(book_text_url, params=params)
            check_for_redirect(book_text_page)
            book_text = book_text_page.text

            page_url = domin + f"/b{book_id}"
            book_page = get_page(page_url)
            soup = BeautifulSoup(book_page.text, 'lxml')
            file_name, photo_url = get_book_characteristic(soup, page_url)

            books_path_file = os.path.join(books_folder_name, f"{file_name}.txt")

            img = get_page(photo_url).content
            parse = urlsplit(photo_url)
            extension = os.path.splitext(parse.path)[-1]

            img_path_file = os.path.join(image_folder_name, f"{file_name}{extension}")

            download_book(book_text, books_path_file)
            download_img(img_path_file, img)

        except requests.exceptions.HTTPError:
            pass

if __name__ == '__main__':
    main()
