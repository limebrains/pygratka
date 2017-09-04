#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import json
import re
import warnings

import ruamel.yaml as yaml
from bs4 import BeautifulSoup
from scrapper_helpers.utils import html_decode, replace_all, _float, _int

from gratka.utils import get_response_for_url

warnings.simplefilter('ignore', yaml.error.UnsafeLoaderWarning)


def get_offer_apartment_details(html_parser):
    """
    This method returns detailed information about the apartment.
    :param html_parser: a BeautifulSoup object
    :rtype: dict
    :return: A dictionary full of details.
    """
    raw_data = html_parser.find(class_="oferta")
    details_dict = {}
    replace_dict = {"\xa0": "", "Negocjuj cenę": "", "\n": ", "}
    while True:
        try:
            if raw_data.find_all("li"):
                item_list = raw_data.find_all("li")
                for detail in item_list:
                    details_dict[detail.span.contents[0]] = replace_all(detail.div.text.strip("\n"), replace_dict)
            else:
                if raw_data.h4.contents[0] == "Opis dodatkowy":
                    raw_data = raw_data.find_next_sibling("div")
                    continue
                item_list = raw_data.find_all("p")
                for detail in item_list:
                    if raw_data.h4.text not in details_dict:
                        details_dict[raw_data.h4.contents[0]] = replace_all(detail.text.strip("\n"), replace_dict)
                    else:
                        details_dict[raw_data.h4.contents[0]] += replace_all(detail.text.strip("\n"), replace_dict)
            raw_data = raw_data.find_next_sibling("div")
        except AttributeError:
            break
    available_from_date = details_dict.get("Wolne od")
    if available_from_date:
        details_dict["Wolne od"] = parse_date_to_timestamp(available_from_date)
    return details_dict


def get_offer_detail_jsons(markup):
    """
    This method creates a list of dictionaries containing any useful details about the apartment.
    :param markup: a requests.response.content object
    :rtype: list(dict)
    :return: A list of dictionaries containing any useful information.
    """
    html_parser = BeautifulSoup(markup, "html.parser")
    found = re.search(r".*dataLayer\s=\s\[(?P<json_info>{(.|\s)*?})\]", markup.decode('utf-8'))
    data_layer = yaml.load(found.groupdict().get("json_info"))
    raw_data = html_parser.find_all("script", {"type": "application/ld+json"})
    detail_jsons = []
    for data in raw_data:
        detail_jsons.append(json.loads(data.text))
    detail_jsons.append(data_layer)
    return detail_jsons[1:]


def get_offer_poster_name(html_parser):
    """
    This method returns the poster's name (and surname if available).
    :param html_parser: a BeautifulSoup object
    :rtype: string
    :return: The poster's name
    """
    poster_name = html_parser.find(class_="posrednikDane")
    return poster_name.b.text if poster_name else ""


def get_offer_company_name(html_parser):
    """
    This method returns the company name if available.
    :param html_parser: a BeautifulSoup object
    :rtype: string
    :return: The company name
    """
    company_name = html_parser.find(class_="nazwaFirmy")
    return company_name.text if company_name else ""


def get_offer_phone_number(html_parser):
    """
    This method extracts the poster's phone number.
    :param html_parser: a BeautifulSoup object
    :rtype: string
    :return: A phone number as string (no spaces, no '+48')
    """
    phone_number = html_parser.find("a", {"id": "mobile-call-button"})
    return phone_number.attrs["href"][4:].replace("+48", "") if phone_number else ""


def get_offer_photos_links(html_parser):
    """
    This method returns a list of links to photos of the apartment.
    :param html_parser: a BeautifulSoup object
    :rtype: list(string)
    :return: A list of links to photos of the apartment
    """
    raw_link_data = html_parser.find(class_="slides links")
    raw_link_data = raw_link_data.find_all("a") if raw_link_data else []
    photos_links = []
    for link in raw_link_data:
        photos_links.append(link.attrs.get("href", ""))
    return photos_links


def get_offer_video_link(html_parser):
    """
    This method returns a link to a video of the apartment.
    :param html_parser: a BeautifulSoup object
    :rtype: string
    :return: A link to a video of the apartment
    """
    raw_link_data = html_parser.find("embed")
    return raw_link_data.attrs.get("src", "")[2:] if raw_link_data else ""


def convert_string_to_date(date_data=""):
    """
    Convert string date description to date str
    :param date_data: Date description
    :type date_data: str
    :return: Date
    :rtype: str
    """
    date_map = {'dzisiaj': 0, 'wczoraj': 1, 'przedwczoraj': 2, 'w tym tygodniu': 6,
                'w ciągu ostatnich dwóch tygodni': 13, 'w tym miesiącu': 20, 'więcej niż miesiąc temu': 40}
    availability_map = {'od zaraz': 0, 'za miesiąc': 30, 'za 3 miesiące': 90, 'za pół roku': 180}
    return (str((dt.datetime.now() - dt.timedelta(days=date_map.get(date_data))).date())
            if date_data in date_map else
            str((dt.datetime.now() + dt.timedelta(days=availability_map.get(date_data))).date())
            if date_data in availability_map else "")


def parse_date_to_timestamp(date):
    """
    Parses string date to unix timestamp
    :param date: Date
    :type date: str
    :return: Unix timestamp
    :rtype: int
    """
    initial = convert_string_to_date(date)
    date_parts = initial.split('-')
    month = int(date_parts[1])
    year = int(date_parts[0])
    day = int(date_parts[2])
    date_added = dt.datetime(year=year, day=day, month=month)
    return int((date_added - dt.datetime(1970, 1, 1)).total_seconds())


def get_offer_details(html_parser):
    """
    This method returns detailed information about the offer.
    :param html_parser: a BeautifulSoup object
    :rtype: dict
    :return: A dictionary containing information about the offer
    """
    raw_detail_data = html_parser.find(class_="statystyki clearOver").find_all("li")
    details = {}
    for detail in raw_detail_data:
        if "Dodano" in detail.text or "Aktualizacja" in detail.text:
            details[detail.contents[0]] = parse_date_to_timestamp(detail.b.text)
        else:
            details[detail.contents[0]] = detail.b.text
    return details


def get_offer_address(html_parser):
    """
    This method returns detailed information about the offer's address.
    :param html_parser: a BeautifulSoup object
    :rtype: string
    :return: A string containing the offer's address
    """
    used = set()
    address = html_parser.title.text.split(" | ")[-1].split(" ")
    unique_address = " ".join([x for x in address if x.strip(",") not in used and (used.add(x) or True)])
    return unique_address


def get_offer_additional_assets(apartment_details):
    additional_assets = apartment_details.get('Dodatkowe zalety', '').split(', ')
    return {
        'heating': ', '.join([asset for asset in additional_assets if 'ogrzewanie' in asset]),
        'balcony': 'balkon' in apartment_details.get('Powierzchnia dodatkowa', ''),
        'kitchen': apartment_details.get('Kuchnia', ''),
        'terrace': 'taras' in apartment_details.get('Powierzchnia dodatkowa', ''),
        'internet': 'internet' in apartment_details.get('Dodatkowe zalety', ''),
        'elevator': 'winda' in apartment_details.get('Dodatkowe zalety', ''),
        'car_parking': 'parking' in apartment_details.get('Garaż/Miejsce parkingowe', ''),
        'disabled_facilities': 'podjazd dla niepełnosprawnych' in additional_assets,
        'mezzanine': 'antresola' in additional_assets,
        'basement': 'piwnica' in apartment_details.get('Powierzchnia dodatkowa', ''),
        'duplex_apartment': 'dwupoziomowe' in apartment_details.get('Liczba poziomów', '') or
                            'wielopoziomowe' in apartment_details.get(
                                'Liczba poziomów', ''),
        'garden': 'ogród' in apartment_details.get('Powierzchnia dodatkowa', ''),
        'garage': 'garaż' in apartment_details.get('Garaż/Miejsce parkingowe', ''),
        'cable_tv': 'TV kablowa' in additional_assets
    }


def get_offer_additional_rent(html_parser):
    try:
        additional_rent_data = html_parser.find(class_='cenaOpis').find(
            lambda x: x.name == 'li' and 'opłaty' in x.text).b.text
    except AttributeError:
        additional_rent_data = ""
    return additional_rent_data


def get_offer_information(url, context=None):
    """
    Scrape detailed information about an Gratka offer.
    :param url: a string containing a link to the offer
    :param context: a dictionary(string, string) taken straight from the :meth:`gratka.category.get_category`
    :returns: A dictionary containing the scraped offer details
    """
    response = get_response_for_url(url)
    content = response.content
    html_parser = BeautifulSoup(content, "html.parser")
    detail_json_list = get_offer_detail_jsons(content)
    offer_apartment_details = get_offer_apartment_details(html_parser)
    return {
        'title': detail_json_list[0].get("name", ""),
        'surface': _float(detail_json_list[1].get("floorSize", "")) or detail_json_list[1].get("floorSize", ""),
        'rooms': detail_json_list[1].get("numberOfRooms", ""),
        'floor': _int(offer_apartment_details.get("Piętro", "")),
        'total_floors': _int(offer_apartment_details.get("Liczba pięter", "")),
        'poster_name': get_offer_poster_name(html_parser),
        'poster_type': detail_json_list[2].get("typ_autora", ""),
        'company_name': get_offer_company_name(html_parser),
        'price': _float(detail_json_list[0]["offers"].get("price", "")),
        'currency': detail_json_list[0]["offers"].get("priceCurrency", ""),
        'additional_rent': _float(get_offer_additional_rent(html_parser)),
        'additional_assets': get_offer_additional_assets(offer_apartment_details),
        'city': detail_json_list[2].get("miejscowosc", ""),
        'district': detail_json_list[2].get("dzielnica", ""),
        'voivodeship': detail_json_list[1]["address"].get("addressRegion", ""),
        'address': get_offer_address(html_parser),
        'geographical_coordinates': (
            detail_json_list[1]["geo"].get("latitude", ""),
            detail_json_list[1]["geo"].get("longitude", "")
        ),
        'phone_numbers': get_offer_phone_number(html_parser),
        'description': html_decode(detail_json_list[0].get("description", "")).replace('\n', ' ').replace('\r', ''),
        'offer_details': get_offer_details(html_parser),
        'photo_links': get_offer_photos_links(html_parser),
        'video_link': get_offer_video_link(html_parser),
        'apartment_details': offer_apartment_details,
        'meta': {
            'is_active': detail_json_list[2].get("czy_aktywne", ""),
            'context': context
        }
    }
