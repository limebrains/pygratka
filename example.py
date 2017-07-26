#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
from gratka import category

log = logging.getLogger(__file__)

SCRAPE_LIMIT = os.environ.get('SCRAPE_LIMIT', None)

if __name__ == '__main__':
    input_dict = {
        # 'minimal_year_built': 2,
        #     'maximal_year_built': 3,
        #     'building_type': [1, 2, 3],
        #     'paid_for': [1, 2],
        #     'rent_time': 3,
        #     'additional_surface': 4,
        #     'levels_count': 1,
        #     'noise_level': 4,
        #     'apartment_state': [1, 2, 3],
        #     'date_added': '4m',
    }
    parsed_category = category.get_category("mieszkania", "do-wynajecia", "pomorskie", "gda", **input_dict)
    print(len(parsed_category))
    print(parsed_category)
