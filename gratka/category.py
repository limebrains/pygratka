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
    """
    This method checks whether the search gave any results.
    :param markup: a requests.response.content object
    :rtype: boolean
    """
    html_parser = BeautifulSoup(markup, "html.parser")
    has_warning = bool(html_parser.find(class_="brakWynikow"))
    return not has_warning


def parse_category_offer(offer_markup):
    """
    A method for getting the most important data out of an offer markup.
    :param offer_markup: a requests.response.content object
    :rtype: dict(string, string)
    :return: see the return section of :meth:`gratka.category.get_category` for more information
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
    pages = html_parser.find(lambda tag: tag.name == 'a' and tag.get('class') == ['strona'])
    return int(pages.text) if pages else 1


def get_category_number_of_pages_from_parameters(region, **filters):
    """A method to establish the number of pages before actually scraping any data"""
    url = url = get_url(region, 1, **filters)
    content = get_response_for_url(url).content
    if not was_category_search_successful(content):
        log.warning("Search for category wasn't successful", url)
        return 0
    return get_category_number_of_pages(content)


def get_distinct_category_page(page, region, **filters):
    """A method for scraping just the distinct page of a category"""
    parsed_content = []
    url = get_url(region, page, **filters)
    content = get_response_for_url(url).content
    if not was_category_search_successful(content):
        log.warning("Search for category wasn't successful", url)
        return []
    parsed_content.extend(parse_category_content(content))

    return parsed_content


def get_category(region, **filters):
    """
    :param region: a string that contains the region name. Districts, cities and voivodeships are supported.
                    The exact location is established using Gratka's API, just as it would happen when typing something
                    into the search bar. Empty string returns results for the whole country. Will be omitted if city
                    present in filters
    :param filters:
    :return: the following dict contains every possible filter (for apartments, houses and rooms) with descriptions of
            its values, but can be empty:

    ::
        input_dict = {
            'category_root':  # int: 100382 = "Nieruchomości"
            'category_changer':  # int:
            For apartments:
            100397 = "na sprzedaż", 100392 = "na sprzedaż/rynek pierwotny", 100393 = "na sprzedaż/rynek wtórny,
            105101 = "na sprzedaż/w programie MdM", 100401 = "do wynajęcia", 105201 = "inne"
            For houses:
            100402 = "na sprzedaż", 100394 = "na sprzedaż/rynek pierwotny", 100395 = "na sprzedaż/rynek wtórny",
            105102 = "na sprzedaż/w programie MdM", 100406 = "do wynajęcia", 105202 = "inne"
            For rooms:
            108251
            'estate_region':  # int, an internal Gratka voivodeship ID
            'city':  # string, name of the city
            'county':  # string, name of the county
            'district':  # string, name of the district
            'street':  #string, name of the street
            'price_from':  # int
            'price_to':  # int
            'acreage_from':  # int
            'acreage_to':  # int
            'room_count_from':  # int from 1 to 21, where 21 means "20 and up"
            'room_count_to':  # int from 1 to 21, where 21 means "20 and up"
            'price_m2_from':  # int
            'price_m2_to':  # int
            'floor_from':  # int from 1 to 33, where 1 is the ground floor, 32 means "above 30" and 33 is the garret
            'floor_to':  # int from 1 to 33, where 1 is the ground floor, 32 means "above 30" and 33 is the garret
            'floor_count_from':  # int, where everything above 30 means "above 30"
            'floor_count_to':  # int, where everything above 30 means "above 30"
            'construction_year_from':  # int: 1 = "okres przedwojenny", 2 = "lata 40", 3 = "lata 50", 4 = "lata 60",
            5 = "lata 70", 6 = "lata 80", 7 = "lata 90", 8 = "lata 2000-2009", 10 = "nowe"
            'construction_year_to':  # int: 1 = "okres przedwojenny", 2 = "lata 40", 3 = "lata 50", 4 = "lata 60",
            5 = "lata 70", 6 = "lata 80", 7 = "lata 90", 8 = "lata 2000-2009", 10 = "nowe"
            'type_of_building[]':  # A list of int, but different values mean different things depending on the category
            For apartments, it looks like this: 1 = "blok", 2 = "kamienica", 3 = "dom wielorodzinny",
            4 = "apartamentowiec", 5 = "wieżowiec"
            For houses: 1 = "wolnostojący", 2 = "segment środkowy", 3 = "segment skrajny", 4 = "bliźniak",
            5 = "pół bliźniaka", 6 = "kamienica", 7 = "willa", 8 = "rezydencja", 9 = "dworek", 10 = "szeregowy",
            11 = "piętro domu", "12 = rekreacyjny"
            'payment_period[]':  # A list of int: 1 = "za miesiąc", 2 = "za dobę"
            'rental_period':  # int: 1 = "pół roku", 2 = "rok", 8 = "ponad rok", 3 = "dwa lata", 4 = "3 lata",
            5 = "dłużej niż 3 lata", 6 = "wakacyjny", 7 = "do uzgodnienia"
            'additional_space[]':  # A list of int: 1 = "loggia", 2 = "balkon", 3 = "drzwi balkonowe", 4 = "taras",
            5 = "komórka lokatorska", 6 = "piwnica", 7 = "strych", 8 = "ogród"
            'level_count':  # int: 1 = "jednopoziomowe", 2 = "dwupoziomowe", 3 = "wielopoziomowe"
            'volume':  # int: 1 = "głośne", 2 = "umiarkowanie głośne", 3 = "umiarkowanie ciche", 4 = "ciche"
            'apartment_condition[]':  # A list of int: 9 = "wysoki standard", 5 = "idealny", 8 = "bardzo dobry",
            12 = "dobry", 1 = "po remoncie", 3 = "odnowione", 10 = "do odświeżenia", 4 = "do odnowienia",
            2 = "do remontu", 7 = "do wykończenia", 6 = "w budowie"
            'period_day':  # string: "1d" = "z ostatnich 24h", "3d" = "z ostatnich 3 dni", "7d" = "z ostatnich 7 dni",
            "14d" = "z ostatnich 14 dni", "1m" = "z ostatniego miesiąca", "3m" = "z ostatnich 3 miesięcy"
            'posted_by[]':  # A list of int: 3 = "biura nieruchomości", 2 = "gazety", 1 = "osoby prywatne", 5 = "inne"
            'keyword':  # string: parts of the description, divided by "," for OR
            'offer_number':  # int, the same as in offer_id (in context)
            'additional_params[]':  # A list of int: 2 = "tylko przetargi", 3 = "tylko z wideo",
            4 = "z lokalizacją na mapie", 5 = "tylko na wyłączność", 6 = "z loznaczone jako "współpracuję""

            # for houses only:

            'plot_acreage_from':  # int
            'plot_acreage_to':  # int
            'garage[]':  # A list of int: 1 = "w budynku", 2 = "wolnostojący", 3 = "wiata", 4 = "jednostanowiskowy",
            5 = "dwustanowiskowy", 6 = "płatny dodatkowo", 7 = "brak"
            'material[]':  # A list of int: 1 = "cegła", 2 = "pustak", 3 = "płyta", 4 = "gazobeton",
            5 = "bloczki", 6 = "silikat", 7 = "drewno", 8 = "mieszany"
            'technology[]':  # A list of int: 1 = "murowana", 2 = "styropianowa", 3 = "kanadyjska", 4 = "Ytong",
            5 = "drewniana", 6 = "szkieletowa"
            'heating[]':  # A list of int: 1 = "CO węglowe", 2 = "CO gazowe", 3 = "CO elektryczne", 4 = "miejskie",
            5 = "olejowe", 6 = "kominek", 7 = "etażowe", 8 = "piec", 9 = "geotermiczne", 10 = "biomasa",
            11 = "podłogowe", 12 = "brak"
            'home_condition[]':  # A list of int: 14 = "wysoki standard", 1 = "idealny", 2 = "bardzo dobry",
            3 = "dobry", 5 = "po remoncie", 7 = "odnowiony", 8 = "do odnowienia", 4 = "do remontu",
            6 = "do wykończenia", 12 = "w budowie", 9 = "stan surowy otwarty", 10 = "stan surowy zamknięty",
            11 = "bez białego montażu", 16 = "stan deweloperski", 17 = "do uzgodnienia", 13 = "do zamieszkania",
            15 = "z lokatorami"

            'acces[]':  # A list of int: 1 = "asfalt", 2 = "utwardzony", 3 = "polny"
            'media[]': # A list of int: 4 = "prąd", 1 = "gaz", 2 = "woda"

            # for rooms only:

            'number_of_people[]':  # A list of int, 1-4 allowed, where 4 is "4 and up"

        }
    """
    page, pages_count, parsed_content = 1, None, []

    while page == 1 or page <= pages_count:
        url = get_url(region, page, **filters)
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
