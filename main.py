import os
import mimetypes
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def set_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=chrome_options)
    print('Selenium Started Successfully')
    return driver


def set_target_info():
    ''' 상세 URL, Base URL, (웹툰 제목 순)'''
    try:
        print("웹툰 상세 페이지 입력")
        url = input()
        parsed = urlparse(url)
        base = parsed.scheme + "://" + parsed.netloc
        return url, base
    except:
        print("input_url parsing error, Exit")
        exit()


# Requests + BS4
def request_page(url):
    html = requests.get(url=url)
    if html.status_code == 200:
        soup = BeautifulSoup(html.text, 'html.parser')
        return soup
    else:
        print("Request Failed, Status: %d" % (html.status_code))
        return None


def get_webtoon_name(page):
    try:
        info_table = page.select_one('table.bt_view1')
        title_tag = info_table.select_one('td.bt_title')
        name = title_tag.string.strip()
        if name != "":
            return title_tag.string.strip()
    except:
        return "WebtoonName_Error"


def get_ch_urls(page):
    ch_table = page.select_one('table.web_list')
    title_tag = ch_table.select('td.content__title')
    ch_urls = []
    for tag in title_tag:
        ch_urls.append(base_url + tag.get('data-role'))
        # Latest Chapter -> First Chapter
    return ch_urls


# Selenium
def get_webtoon_img_urls(_url):
    try:
        driver.get(_url)
        div_toon_img = driver.find_element(by=By.ID, value="toon_img")
        img_tags = div_toon_img.find_elements(by=By.TAG_NAME, value='img')

        images_url = []
        for img in img_tags:
            images_url.append(img.get_attribute('src'))
    except:
        print("webtoon url crawling error")
        return []
    return images_url


# By Chapter
def download_images(_urls):
    title = driver.title
    folder_path = f'./{webtoon_name}/{driver.title}'.translate(
        str.maketrans('', '', "\\:?\"<>|"))
    os.makedirs(folder_path, exist_ok=True)

    count = 1
    print(f'CHAPTER: {title}\n\n')

    urls = _urls
    for url in urls:
        start = time.time()
        img = requests.get(url)
        content_type = img.headers['content-type']
        extension = mimetypes.guess_extension(content_type)

        # file_path = f"{folder_path}/{count}.{extension}"
        file_path = folder_path + "/{0:03d}".format(count) + extension
        print(file_path)
        count += 1
        with open(file_path, 'wb') as f:
            f.write(img.content)
        print(f'{count-1}/{len(urls)} => {time.time() - start} seconds')

    print('\n')
    return


driver = set_chrome_driver()

while (True):
    input_url, base_url = set_target_info()
    driver = set_chrome_driver()
    bs4_soup = request_page(input_url)
    if bs4_soup is None:
        print("Requested Html Error (NONE)")
        exit()

    webtoon_name = get_webtoon_name(bs4_soup).translate(
        str.maketrans('', '', "\\:?\"<>|"))
    chapter_urls = get_ch_urls(bs4_soup)

    print("%s Downloading Start\n" % (webtoon_name))
    for chapter_url in chapter_urls:
        print(f"Get Chapter's Urls...\n")
        image_urls = get_webtoon_img_urls(chapter_url)

        print("Ok. Ready Image...\n")
        download_images(image_urls)

        print(f'{chapter_url} Passed\n\n')

    print("Again? Y / N")
    answer = input()
    if answer == "Y" or answer == 'y':
        continue
    else:
        break

exit()
