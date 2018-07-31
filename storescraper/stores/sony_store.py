import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class SonyStore(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'Tablet',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['televisores-y-teatro-en-casa/televisores', 'Television'],
            ['celulares-y-tablets/smartphones-xperia', 'Cell'],
            ['camaras/cyber-shot', 'Camera'],
            ['audio/sistemas-de-audio', 'StereoSystem'],
            ['televisores-y-teatro-en-casa/reproductores-de-blu-ray-disc'
             '-y-dvd', 'OpticalDiskPlayer'],
            ['televisores-y-teatro-en-casa/teatro-en-casa', 'StereoSystem'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'https://store.sony.cl/{}?PS=48'.format(
                category_path)

            soup = BeautifulSoup(session.get(category_url, verify=False).text,
                                 'html.parser')

            containers = soup.findAll('div', 'prod')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for product_container in containers:
                product_url = product_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url, verify=False).text

        pricing_data = re.search(r'vtex.events.addData\(([\S\s]+?)\);',
                                 page_source).groups()[0]
        pricing_data = json.loads(pricing_data)

        skus_data = re.search(r'var skuJson_0 = ([\S\s]+?);',
                              page_source).groups()[0]
        skus_data = json.loads(skus_data)
        name = '{} {}'.format(pricing_data['productBrandName'],
                              pricing_data['productName'])
        price = Decimal(pricing_data['productPriceTo'])

        soup = BeautifulSoup(page_source, 'html.parser')

        picture_urls = [tag['rel'][0] for tag in
                        soup.findAll('a', {'id': 'botaoZoom'})]

        description = html_to_markdown(
            str(soup.find('div', 'section-specifications')))

        products = []

        if 'productEans' in pricing_data:
            ean = pricing_data['productEans'][0]
            if len(ean) == 12:
                ean = '0' + ean
            if not check_ean13(ean):
                ean = None
        else:
            ean = None

        for sku_data in skus_data['skus']:
            sku = str(sku_data['sku'])
            stock = pricing_data['skuStocks'][sku]
            sku_name = '{} / {}'.format(name, sku_data['skuname'])

            p = Product(
                sku_name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                ean=ean,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
