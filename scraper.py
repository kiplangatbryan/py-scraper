#!/bin/python3

from bs4 import BeautifulSoup
import requests
import json
from threading import Thread
from time import sleep
from random import randint
import sys
import argparse


# visit the url and get links to all the products on root page

class Scraper:
    def __init__(self,url, to_file):
        main_url = url
        self.root_ = requests.get(main_url)
        self.threads = []
        self.data = []
        self.to_file = to_file

        print('Fetching urls ...')

        self.urls = self.getUrls()
        print(f'Found {len(self.urls)} urls ...')
        print('processing urls ...')
        self.init()

    def getUrls(self) -> list:
        try:
            shop_data = BeautifulSoup(self.root_.text, 'lxml')
            product = shop_data.select('a.woocommerce-loop-product__link')
            return ['%s' % (url.get('href')) for url in product]
        except (ConnectionError, ConnectionAbortedError) as e:
            print('Connection Err')
            sys.exit(1)
        except KeyboardInterrupt as e:
            print('closing ..')
            sys.exit(1)

    # loop through all the links and fetch all the details

    def fetch_data(self, url) -> list:
        try:
            page = requests.get(url, allow_redirects=True)
        except ConnectionError as e:
            print(e)
            sys.exit(1)
        except KeyboardInterrupt as e:
            print('closing ..')
            sys.exit(1)

        product_data = BeautifulSoup(page.text, 'lxml')

        # get title
        title = product_data.select('.product_title')[0].getText()
        price = product_data.select('p.price .amount bdi')[0].text
        features = [prod_desc.getText() for prod_desc in product_data.select(
            '.markup > ul > li')]

        description = product_data.select('#tab-description p')[0].getText()

        image_url = product_data.select(
            '.woocommerce-product-gallery__image a')[0].get('href')

        return {
            'title': title,
            'price': price,
            'image_url': image_url,
            'features': features,
            'description': description
        }

    def write_to_file(self, data) -> None:
        with open(self.to_file, 'w') as f:
            json.dump(data, f)
        print('data written to file ... [data.json]')

    def downloadThread(self, start, end):
        for i in range(start, end):
            data = self.fetch_data(self.urls[i])
            self.data.append(data)

    def rangeCheck(self, total, current):
        if (total - current) > 5:
            return current + 4
        else:
            return total - current

    def joinThreads(self):
        for i, thread in enumerate(self.threads):
            thread.join()
        print('writing to file ...')
        self.write_to_file(self.data)
        print('process terminated successfully ...')

    def init(self):
        for i in range(0, len(self.urls), 5):
            urlThread = Thread(target=self.downloadThread, args=(
                i, self.rangeCheck(len(self.urls), i)))
            urlThread.start()
            self.threads.append(urlThread)
        self.joinThreads()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a simple scraper')
    parser.add_argument('--h', help='host or url', type=str, dest='host')
    parser.add_argument('--f', help='name of the json file', dest='file')

    data = parser.parse_args()
    Scraper(data.host, data.file)
