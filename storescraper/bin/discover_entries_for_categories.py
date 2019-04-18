import argparse
import json
import logging
import sys
sys.path.append('../..')

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='discover_urls_for_categories.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Discovers the URLs of the given store and (optional) '
                    'categories')

    parser.add_argument('store', type=str,
                        help='The name of the store to be parsed')

    parser.add_argument('--categories', type=str, nargs='*',
                        help='Specific categories to be parsed')

    parser.add_argument('--with_async', type=bool, nargs='?', default=False,
                        const=True,
                        help='Use asynchronous tasks (celery)')

    parser.add_argument('--extra_args', type=json.loads, nargs='?', default={},
                        help='Optional arguments to pass to the parser '
                             '(usually username/password) for private sites)')

    args = parser.parse_args()
    store = get_store_class_by_name(args.store)

    result = store.discover_entries_for_categories(
        categories=args.categories,
        use_async=args.with_async,
        extra_args=args.extra_args)

    for entry in result:
        print('\n{} ({})'.format(entry['url'], entry['category']))
        positions = entry['positions']

        if positions:
            print('Positions:')
            for position in positions:
                print('* {} in {} ({})'.format(position['value'],
                                               position['section_name'],
                                               position['section_url']))
        else:
            print('No positions given')

    print('Total: {} URLs'.format(len(result)))


if __name__ == '__main__':
    main()