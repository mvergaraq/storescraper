import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class JumboColombia(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['C:/47/48/54/', 'ExternalStorageDrive'],
            ['C:/47/2000061/1000020/', 'MemoryCard'],
        ]

        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            session = session_with_proxy(extra_args)
            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)
                category_url = 'http://www.tiendasjumbo.co/buscapagina?fq={}' \
                               '&PS=50&sl=19ccd66b-b568-43cb-a106-b52f9796f5' \
                               'cd&cc=24&sm=0&PageNumber={}'.format(
                                category_path, page)

                base_soup = BeautifulSoup(session.get(category_url).text,
                                          'html.parser')

                link_containers = base_soup.findAll('article')

                if not link_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

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
            str(soup.find('section', 'product-specs')))
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

            if sku_data['sellerId'] == 'lojamultilaser':
                price = (price * Decimal('0.95')).quantize(Decimal('0.01'))

            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'COP',
                sku=sku,
                ean=ean,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products