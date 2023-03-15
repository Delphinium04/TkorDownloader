import os
import mimetypes
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def set_chrome_driver():
    # OLD
    # driver = webdriver.Chrome(executable_path="./chromedriver", options=chrome_options)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    print('Selenium Started')
    return driver


def check_url_validity(url):
    parsed = urlparse(url)
    base = parsed.scheme + "://" + parsed.netloc
    if parsed.scheme == '' or parsed.netloc == '':
        return ""
    return base


# Requests + BS4
def request_page(url):
    html = requests.get(url=url)
    if html.status_code == 200:
        soup = BeautifulSoup(html.text, 'html.parser')
        return soup
    else:
        print("Request Failed, Status: %d" % html.status_code)
        return None


def get_webtoon_name(page):
    info_table = page.select_one('table.bt_view1')
    title_tag = info_table.select_one('td.bt_title')
    name = title_tag.string.strip()
    if name != "":
        return title_tag.string.strip()
    else:
        print("Couldn't get webtoon name")
        exit()


def get_ch_urls(page):
    ch_table = page.select_one('table.web_list')
    title_tag = ch_table.select('td.content__title')

    ch_urls = []
    for tag in title_tag:
        ch_urls.append(base_url + tag.get('data-role'))
        # Download recent Chapter to old chapter, descending
    ch_urls.reverse()
    return ch_urls


# Selenium
def get_webtoon_img_urls(_url):
    driver.get(_url)
    div_toon_img = driver.find_element(by=By.ID, value="toon_img")
    img_tags = div_toon_img.find_elements(by=By.TAG_NAME, value='img')

    if img_tags:
        images_url = []
        for img in img_tags:
            images_url.append(img.get_attribute('src'))
        return images_url
    else:
        print("Couldn't get images url")
        return []


# By Chapter
def download_images(_urls, count):
    title = driver.title
    folder_path = './{0}/{1:03d}-{2}'.format(webtoon_name, count, title)
    folder_path = folder_path.translate(str.maketrans('', '', "\\:?\"<>|"))
    if os.path.isdir(folder_path):
        print('폴더 존재 존재');
        exist_file_list = os.listdir(folder_path)
        if len(exist_file_list) == len(_urls):
            print("파일 존재, 다음 화 스킵")
            return
        else:
            print("강제 다운로드")
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
        print(f'{count - 1}/{len(urls)} => {time.time() - start} seconds')

    print('\n')
    return


if __name__ == '__main__':
    driver = set_chrome_driver()

    while True:
        print("주소를 입력 (예시: https://toonkorXXX.com/???)")
        user_input = input()
        base_url = check_url_validity(user_input)

        if base_url == "":
            print("URL 오류, 다시 입력")
            continue

        driver = set_chrome_driver()
        bs4_soup = request_page(user_input)
        if bs4_soup is None:
            print("bs4 request_page error")
            continue

        webtoon_name = get_webtoon_name(bs4_soup)
        chapter_urls = get_ch_urls(bs4_soup)
        print("%s Downloading Start\n" % webtoon_name)

        chapter_count = 1
        for chapter_url in chapter_urls:
            print(f"Get Chapter's Urls")
            image_urls = get_webtoon_img_urls(chapter_url)
            print("Downloading Image")
            download_images(image_urls, chapter_count)
            print(f'\n{chapter_url} Passed\n')
            chapter_count = chapter_count + 1

        print("Again? Y / N")
        answer = input()
        if answer == "Y" or answer == 'y':
            continue
        else:
            break

