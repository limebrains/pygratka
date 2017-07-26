#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import logging
import sys
from bs4 import BeautifulSoup

from gratka import BASE_URL, WHITELISTED_DOMAINS
from gratka.utils import get_response_for_url, get_url

if sys.version_info < (3, 3):
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

log = logging.getLogger(__file__)


def was_category_search_successful(markup):
    html_parser = BeautifulSoup(markup, "html.parser")
    has_warning = bool(html_parser.find(class_="brakWynikow"))
    return not has_warning


def parse_category_offer(offer_markup):
    """
    A method for getting the most important data out of an offer markup.
    :param offer_markup: a requests.response.content object
    :rtype: dict(string, string)
    :return: see the return section of :meth:`scrape.category.get_category` for more information
    """
    html_parser = BeautifulSoup(offer_markup, "html.parser")
    link = html_parser.find("a")
    url = "{0}{1}".format(BASE_URL, link.attrs['href'])
    offer_id = json.loads(html_parser.find('li').attrs['data-ogloszenie'].replace("'", '"'))["id_ogl"]
    offer_position = html_parser.find('li').attrs['data-pozycja']
    offer_points = html_parser.find('li').attrs['data-punkty-wyroznienia']
    if not url:
        # detail url is not present
        return {}
    if urlparse(url).hostname not in WHITELISTED_DOMAINS:
        # domain is not supported by this backend
        return {}
    return {
        'detail_url': url,
        'offer_id': offer_id,
        'offer_position': offer_position,
        'offer_points': offer_points
    }


def parse_category_content(markup):
    """
    A method for getting a list of all the offers found in the markup.
    :param markup: a requests.response.content object
    :rtype: list(requests.response.content)
    """
    html_parser = BeautifulSoup(markup, "html.parser")
    offers = html_parser.find_all("li", {"data-gtm": "zajawka"})
    parsed_offers = [
        parse_category_offer(str(offer)) for offer in offers
    ]
    return parsed_offers


def get_category_number_of_pages(markup):
    """
    A method that returns the maximal page number for a given markup, used for pagination handling.
    :param markup: a requests.response.content object
    :rtype: int
    """
    html_parser = BeautifulSoup(markup, "html.parser")
    pages = html_parser.find(lambda tag: tag.name == 'a' and tag.get('class') == ['strona']).text
    return int(pages) if pages else 1


def get_category(main_category, detail_category, voivodeship, region, **filters):
    """

    :param main_category: "mieszkania", "domy", "dzialki-grunty", "lokale-obiekty", "garaze", "pokoje-do-wynajecia" or "inwestycje"
    :param detail_category: "do-wynajecia", "sprzedam" or "inne", doesn't apply when main_category is "inwestycje" or "pokoje-do-wynajecia"
    :param voivodeship: any existing Polish vooivodeship
    :param region: a string that contains the region name. Districts, cities and voivodeships are supported. The exact location is established using Gratka's API, just as it would happen when typing something into the search bar. Empty string returns results for the whole country.
    :param filters:
    :return: the following dict contains every possible filter with examples of its values, but can be empty:

    ::
        input_dict = {
            'minimal_price':
            'maximal_price':
            'minimal_surface':
            'maximal_surface':
            'minimal_room_count':
            'maximal_room_count':
            'minimal_price_per_square_meter':
            'maximal_price_per_square_meter':
            'minimal_floor':
            'maximal_floor':
            'minimal_year_built':
            'maximal_year_built':
            'building_type': list
            'paid_for': list
            'rent_time':
            'additional_surface':
            'levels_count':
            'noise_level':
            'apartment_state': list
            'date_added':
            'added_by_agency':
            'added_by_newspaper':
            'added_by_private':
            'added_by_other':
            'keywords': list
            'offer_number':
            'tenders_only':
            'with_video_only':
            'with_map_localization_only':
            'exclusive_only':
            'marked_as_cooperating':

            # for houses only:

            'minimal_allotment_surface':
            'maximal_allotment_surface':
            'garage_type': list
            'building_material': list
            'building_technology': list
            'heating_type': list
            'state': list
            'access': list
            'utilities': list

            # for rooms only:

            'number_of_people':

        }
    """
    page, pages_count, parsed_content = 1, None, []

    while page == 1 or page <= pages_count:
        url = get_url(main_category, detail_category, voivodeship, region, page, **filters)
        log.info(url)
        content = get_response_for_url(url).content
        if not was_category_search_successful(content):
             log.warning("Search for category wasn't successful", url)
             return []

        parsed_content.extend(parse_category_content(content))
        
        if page == 1:
            pages_count = get_category_number_of_pages(content)
            if page == pages_count:
                break

        page += 1

    return parsed_content
