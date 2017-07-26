#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import requests
import unicodedata
from scrapper_helpers.utils import caching
try:
    from __builtin__ import unicode
except ImportError:
    unicode = lambda x, *args: x

from gratka import BASE_URL

log = logging.getLogger(__file__)

FILTER_MAP = {
    'minimal_price': 'co', 'maximal_price': 'cd', 'minimal_surface': 'mo', 'maximal_surface': 'md',
    'minimal_room_count': 'lpo', 'maximal_room_count': 'lpd', 'minimal_price_per_square_meter': 'cmo',
    'maximal_price_per_square_meter': 'cmd', 'minimal_floor': 'po', 'maximal_floor': 'pd','minimal_floor_count': 'lo',
    'maximal_floor_count': 'ld', 'minimal_year_built': 'rbo', 'maximal_year_built': 'rbd', 'building_type': 'tb',
    'paid_for': 'pz', 'rent_time': 'ow', 'additional_surface': 'pod', 'levels_count': 'lpz', 'noise_level': 'gl',
    'apartment_state': 'sm', 'date_added': 'od', 'added_by_agency': 'za', 'added_by_newspaper': 'zg',
    'added_by_private': 'zi', 'added_by_other': 'zin', 'keywords': 'sk', 'offer_number': 'no', 'tenders_only': 'tp',
    'with_video_only': 'tw', 'with_map_localization_only': 'lnm', 'exclusive_only': 'twy',
    'marked_as_cooperating': 'twsp', 'minimal_allotment_surface': 'pdo', 'maximal_allotment_surface': 'pdd',
    'garage_type': 'ga', 'building_material': 'ma', 'building_technology': 'te', 'heating_type': 'ogr',
    'state': 'std', 'access': 'doj', 'utilities': 'me', 'number_of_people': 'losb'
}


def replace_all(list, dic):
    """
    This method returns the input list, but replaces its elements according to the input dictionary.
    :param list: input list
    :param dic: dictionary containing the changes. key is the character that's supposed to be changed and value is
    the desired value
    :rtype: list
    :return: List with the according elements replaced
    """
    for i, element in enumerate(list):
        list[i] = dic[element]
    return list


def normalize_text(text, lower=True, replace_spaces='_'):
    """
    This method returns the input string, but normalizes is it for use in the url.
    :param text: input string
    :rtype: string
    :return: Normalized string. lowercase, no diacritics, '-' instead of ' '
    """
    try:
        unicoded = unicode(text, 'utf8')
    except TypeError:
        unicoded = text
    if lower:
        unicoded = unicoded.lower()
    normalized = unicodedata.normalize('NFKD', unicoded)
    encoded_ascii = normalized.encode('ascii', 'ignore')
    decoded_utf8 = encoded_ascii.decode("utf-8")
    if replace_spaces:
        decoded_utf8 = decoded_utf8.replace(" ", replace_spaces)
    return decoded_utf8


def get_region_from_autosuggest(region_part):
    """
    This method makes a request to the OtoDom api, asking for the best fitting region for the supplied region_part string.
    :param region_part: input string, it should be a part of an existing region in Poland, either city, street, district or voivodeship
    :rtype: dict
    :return: A dictionary which contents depend on the API response.
    """
    if not region_part:
        return {}
    url = u"http://www.gratka.pl/b-dom/ajax/podpowiedzi-lokalizacja/?tekst={0}".format(region_part)
    response = json.loads(get_response_for_url(url).text)[0]

    region_dict = {}

    if "powiat" in response:
        region_dict["county"] = normalize_text(response["powiat"])
    if "miejscowosc" in response:
        region_dict["city"] = normalize_text(response["miejscowosc"])
    if "ulica" in response:
        region_dict["street"] = normalize_text(response["ulica"])
    if "dzielnica" in response:
        region_dict["district"] = normalize_text(response["dzielnica"])

    return region_dict


def get_url(main_category, detail_category, voivodeship, region, page=1, **filters):
    """
    This method builds a ready-to-use url based on the input parameters.
    :param main_category: see :meth:`gratka.category.get_category` for reference
    :param detail_category: see :meth:`gratka.category.get_category` for reference
    :param region: see :meth:`gratka.category.get_category` for reference
    :param page: page number
    :param filters: see :meth:`scrape.category.get_category` for reference
    :rtype: string
    :return: the url
    """
    if main_category != "inwestycje" and main_category != "pokoje-do-wynajecia":
        detail_category = "-".join([main_category, detail_category])
    else:
        detail_category = main_category
    region_dict = get_region_from_autosuggest(region)
    basic_url = "/".join([BASE_URL, detail_category, "lista"]) + "/" + ",".join([voivodeship, region_dict.get("city", "")])
    filters_value_list = list(filters.values()) + [page]
    filters_key_list = replace_all(list(filters.keys()), FILTER_MAP) + ['s']
    for i, value in enumerate(filters_value_list):
        if isinstance(value, list):
            filters_value_list[i] = "_".join([str(x) for x in value])
    filter_url = ",".join([basic_url] + [str(x) for x in filters_value_list] + [str(x) for x in filters_key_list]) + ".html"
    return filter_url


@caching
def get_response_for_url(url):
    """
    :param url: an url, most likely from the :meth:`gratka.utils.get_url` method
    :return: a requests.response object
    """
    return requests.get(url)
