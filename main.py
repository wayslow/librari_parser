import os
import pathlib
from itertools import count
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

names_list = []


def get_page(page_url, params=None):
    response = requests.get(page_url, params)
    response.raise_for_status()

    return response


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def get_book_name(soup):
    title_tag = soup.find('h1')
    book_name = sanitize_filename("_".join(title_tag.text.split('   ::   ')[0].split(" ")).strip())

    book_name = check_same_name(book_name)

    return book_name


def get_photo_url(page_url, soup, filename, folder_name):
    img = get_page(photo_url).content
    parse = urlsplit(photo_url)
    extension = os.path.splitext(parse.path)[-1]

    path = os.path.join(folder_name, f"{filename}{extension}")
    return path
    '''with open(path, 'wb') as file:
        file.write(img)'''


def get_comments(soup):
    comments = []
    comments_tags = soup.find_all("span", class_="black")
    print(comments_tags)
    for coment_tag in comments_tags:
        comments.append(coment_tag.text)
    return comments


def check_same_name(book_name):
    verifiable_book_name = book_name

    for index in count(1):

        if verifiable_book_name in names_list:
            verifiable_book_name = f"{book_name}_{str(index)}"
        else:
            names_list.append(verifiable_book_name)
            break

    return verifiable_book_name


def parse_book_page(book_id, domin, image_folder_name):
    path = f"/b{book_id}"
    page_url = domin + path

    page = get_page(page_url, )
    soup = BeautifulSoup(page.text, 'lxml')

    book_name = get_book_name(soup)

    photo_url = urljoin(page_url, soup.find("div", class_="bookimage").find('img')['src'])

    genre = soup.find("span", class_="d_book").find("a").text

    comments = get_comments(soup)
    book_info = {
        "book_name": book_name,
        "photo_url": photo_url,
        "genre": genre,
        "comments": comments,
    }
    return book_info


def download_book(domin, book_id, books_folder_name, image_folder_name):
    params = {
        "id": book_id,
    }

    path = "/txt.php"

    url = domin + path

    try:
        response = get_page(url, params=params)
        check_for_redirect(response)

        book_info = parse_book_page(book_id, domin, image_folder_name)

        books_path_file = os.path.join(books_folder_name, f"{book_info['book_name']}.txt")

        # with open(books_path_file, "w", encoding="utf-8") as book:
        #    book.write(response.text)

    except requests.exceptions.HTTPError:
        pass


def main():
    books_folder_name = "books"
    pathlib.Path(books_folder_name).mkdir(parents=True, exist_ok=True)

    image_folder_name = "imge"
    pathlib.Path(image_folder_name).mkdir(parents=True, exist_ok=True)

    for book_id in range(1, 10):
        domin = 'https://tululu.org'
        download_book(domin, book_id, books_folder_name, image_folder_name)


if __name__ == '__main__':
    main()
