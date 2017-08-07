#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os

from gratka.category import get_category
from gratka.offer import get_offer_information

log = logging.getLogger(__file__)

SCRAPE_LIMIT = os.environ.get('SCRAPE_LIMIT', None)

if __name__ == '__main__':
    input_dict = {'category_changer': 100401, 'category_root': 100382,}

    if os.getenv('PRICE_TO'):
        input_dict['price_to'] = os.getenv('PRICE_TO')

    parsed_category = get_category("gda", **input_dict)

    log.info("Offers in that category - {0}".format(len(parsed_category)))

    if SCRAPE_LIMIT:
        parsed_category = parsed_category[:int(SCRAPE_LIMIT)]
        log.info("Scraping limit - {0}".format(len(parsed_category)))

    for offer in parsed_category:
        log.info("Scraping offer - {0}".format(offer['detail_url']))
        try:
            offer_detail = get_offer_information(offer['detail_url'], context=offer)
        except IndexError:
            log.info("Offer not available- {0}".format(offer_detail))
        else:
            log.info("Scraped offer - {0}".format(offer_detail))
