#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
import pickle
import sys
from bs4 import BeautifulSoup

import gratka.category as category
import gratka.offer as offer
import gratka.utils as utils

if sys.version_info < (3, 3):
    from mock import mock
else:
    from unittest import mock
REGIONS_TO_TEST = [
    "Gdań", "Sop", "Oliw", "Wrzeszcz", "czechowice", "Nowa Wieś", "pomorskie", "Książąt pomor sopot", ""
]
ACTUAL_REGIONS = [
    {'estate_region': 11, 'city': 'gdansk'}, {'estate_region': 11, 'city': 'sopot'},
    {'estate_region': 11, 'district': 'brama_oliwska', 'city': 'gdansk'},
    {'estate_region': 11, 'city': 'gdansk', 'district': 'wrzeszcz'},
    {'district': 'czechowice_dolne', 'city': 'czechowice-dziedzice', 'estate_region': 12},
    {'city': 'polska_nowa_wies', 'street': 'nowa', 'estate_region': 3},
    {'city': 'brody_pomorskie', 'estate_region': 11, 'county': 'tczewski'},
    {'city': 'sopot', 'estate_region': 11, 'street': 'ksiazat_pomorskich'}, {}
]


def test_get_region_from_autosuggest():
    with mock.patch("gratka.utils.json.loads") as json_loads:
        utils.get_region_from_autosuggest("gda")
        assert json_loads.called


def test_get_url():
        with mock.patch("gratka.utils.get_region_from_autosuggest") as get_region_from_autosuggest,\
                mock.patch("gratka.utils.get_url_from_mapper") as get_url_from_mapper:
            get_region_from_autosuggest.return_value = ACTUAL_REGIONS[0]
            get_url_from_mapper.return_value = "http://dom.gratka.pl//mieszkania-do-wynajecia/lista/pomorskie.html"
            utils.get_url("test", {})
            assert get_region_from_autosuggest.called
            assert get_url_from_mapper.called


def test_get_url_from_mapper():
    with mock.patch("gratka.utils.requests.request") as request, \
            mock.patch("gratka.utils.json.loads") as loads:
        utils.get_url_from_mapper({})
        assert request.called
        assert loads.called


def test_get_response_for_url():
    with mock.patch("gratka.utils.requests.get") as get:
        utils.get_response_for_url("")
        assert get.called


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize(
    'markup_path,expected_value', [
        ("test_data/markup_offer", {
        'detail_url': "http://dom.gratka.pl//tresc/401-64064026-pomorskie-gdansk-obroncow-wybrzaza.html",
        'offer_id': "64064026",
        'offer_position': "1",
        'offer_points': "25"
    })
    ])
def test_parse_category_offer(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert category.parse_category_offer(pickle.load(markup_file)) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [("test_data/markup_offer", [
    {'detail_url': 'http://dom.gratka.pl//tresc/401-64064026-pomorskie-gdansk-obroncow-wybrzaza.html',
     'offer_id':'64064026',
     'offer_points': '25',
     'offer_position': '1'}
])])
def test_parse_category_content(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert category.parse_category_content(pickle.load(markup_file)) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value',
                         [("test_data/markup_offers", 38), ("test_data/markup_no_offers", 1)])
def test_get_category_number_of_pages(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert category.get_category_number_of_pages(pickle.load(markup_file)) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value',
                         [("test_data/markup_offers", True), ("test_data/markup_no_offers", True)])
def test_was_category_search_successful(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert category.was_category_search_successful(pickle.load(markup_file)) == expected_value


def test_get_category():
    with mock.patch("gratka.category.get_url") as get_url,\
            mock.patch("gratka.category.get_response_for_url") as get_response_for_url,\
            mock.patch("gratka.category.was_category_search_successful") as was_category_search_successful,\
            mock.patch("gratka.category.parse_category_content") as parse_category_content,\
            mock.patch("gratka.category.get_category_number_of_pages", return_value=1) as get_category_number_of_pages:
        category.get_category("")
        assert get_url.called
        assert get_response_for_url.called
        assert was_category_search_successful.called
        assert parse_category_content.called
        assert get_category_number_of_pages.called


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [("test_data/offer", 'Agnieszka Flitta')])
def test_get_offer_poster_name(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_poster_name(BeautifulSoup(pickle.load(markup_file), "html.parser")) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [
    ("test_data/offer", [
        {'offers': {'@type': 'Offer', 'price': '25', 'priceCurrency': 'PLN'},
         'url': 'http://dom.gratka.pl/tresc/401-73379581-pomorskie-gdansk-kokoszki-fundamentowa.html',
         'name': 'Mieszkanie Gdańsk Kokoszki, ul. Fundamentowa',
         'image': 'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425827_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
         'description': 'Mieszkania dlapracowników na KOKOSZKACH ! ! !\r\n\r\nProponujemy Państwu ofertę najmu 6 '
                        'mieszkań przystosowanych dla pracowników. W każdym znajduje się 8 miejsc noclegowych '
                        '(razem 48 miejsc).\r\n\r\nNieruchomości położone są w osobnych blokach na jednym osiedlu '
                        'tuż za Trójmiejską Obwodnicą.\r\n\r\nIstnieje możliwość powiększenia ilości miejsc o kolejne '
                        '17 łóżek, które znajdują się w willi na sąsiednim osiedlu.\r\n\r\nKażde z mieszkań składa się '
                        'z:\r\n\r\n- 3 pokoi,\r\n\r\n- kuchni,\r\n\r\n- łazienki,\r\n\r\n- wc,\r\n\r\n- przedpokoju.\r\n\r\n'
                        'Miesięczny czynsz najmu zawiera się w przedziale od25 zł do 40 zł za osobodobę.\r\n\r\n'
                        'Dodatkowym jednorazowym kosztem jest jednomiesięczna kaucja.\r\n\r\nPreferowany najem długookresowy!'
                        '\r\n\r\nSERDECZNIE POLECAM ! ! !', '@context': 'http://schema.org', '@type': 'IndividualProduct',
         'category': 'mieszkanie'}, {'geo': {'latitude': 54.3548, '@type': 'GeoCoordinates', 'longitude': 18.4947},
          'address': {'@type': 'PostalAddress', 'addressCountry': 'Polska',
        'addressRegion': 'pomorskie', 'addressLocality': 'Gdańsk Kokoszki', 'streetAddress': 'FUNDAMENTOWA'},
        'floorSize': '60', 'numberOfRooms': 3, '@context': 'http://schema.org', '@type': 'Apartment'},
        {'liczba_zdjec': 10, 'miejscowosc': 'Gdańsk', 'id_kategoria': 401, 'id_autor': 1006,
         'tytul': 'Mieszkanie 3-pokojowe, 60m2', 'kategoria_pelna': 'Dom - Mieszkania - Rynek wtórny - mam do wynajęcia',
         'url': 'http://dom.gratka.pl/tresc/401-73379581-pomorskie-gdansk-kokoszki-fundamentowa.html',
         'punkty_wyroznienia': 3, 'region': 'pomorskie', 'czy_aktywne': '1', 'dzielnica': 'Kokoszki', 'rodzaj': '',
         'zdjecie': 'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425827_mieszkanie-gdansk-kokoszki-ul-fundamentowa_w.jpg',
         'cookie_uzytkownika': '5979c79b4a1a21.40046566', 'id_eav': 73379581, 'nazwa_kategorii': 'Mieszkania do wynajęcia',
         'id_inwestycja': '', 'cena': 25, 'id_ogloszenie': 73379581, 'data_publikacji': '2017-07-18 23:02:11',
         'typ_autora': 'Biuro nieruchomości', 'kategoria_glowna': 'Dom', 'typ_strony': 'karta-ogloszenia'}]
)
])
def test_get_offer_detail_jsons(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_detail_jsons(pickle.load(markup_file)) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [
    ("test_data/offer", {'Dodano: ': 1503360000, 'Rynek: ': 'wtórny', 'Liczba odsłon: ': '140',
                         'Źródło: ': 'Biuro nieruchomości', 'Aktualizacja: ': 1504483200}
)
])
def test_get_offer_details(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_details(BeautifulSoup(pickle.load(markup_file), "html.parser")) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [("test_data/offer", "")])
def test_get_offer_video_link(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_video_link(BeautifulSoup(pickle.load(markup_file), "html.parser")) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [
    ("test_data/offer", [
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425827_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425829_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425831_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425833_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425835_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425837_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425839_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425841_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425843_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg',
        'https://d-gd.ppstatic.pl/kadry/k/r/gd-ogl/1c/7d/73379581_55425845_mieszkanie-gdansk-kokoszki-ul-fundamentowa.jpg'
    ])
])
def test_get_offer_photos_links(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_photos_links(BeautifulSoup(pickle.load(markup_file), "html.parser")) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [("test_data/offer", {'Powierzchnia': '60 m2',
        'Sport': 'Marlin - Akademia Pływania Sylwia Kula-Gdaniec - 100m, '
        'Marlin - Akademia Pływania Sylwia Kula-Gdaniec Szkółki w Kartuzach - 100m',
        'Zakupy': 'LEROY MERLIN - 1,8km, Leroy Merlin Polska Spółka z o.o. - 1,8km',
        'Cena': '25 zł', 'Kuchnia': 'z oknem, oddzielna, z wyposażeniem, w zabudowie',
        'Powierzchnia dodatkowa': 'balkon', 'Numer oferty': 'gratka-ZA013701',
        'Administracja i instytucje publiczne': 'Urząd Pocztowy Gdańsk 43 - 1,4km, Kościół pw. św. Brata Alberta Chmielowskiego - 600m',
        'Liczba pokoi': '3', 'Typ budynku': 'blok', 'Edukacja': 'Szkoła Podstawowa nr 83  - 900m, Szkoła Podstawowa nr 84  - 1,9km',
        'Kultura i sztuka': 'photo-travels - 1,6km', 'Garaż/Miejsce parkingowe': 'brak',
        'Zdrowie': 'Jacek Rogoń Spec. chirurgii dziecięcej - 1,4km, Ljósheim Anna, lek. stomatolog Gabinet - 1,1km',
        'Dodatkowe zalety': 'winda, ogrzewanie miejskie',
        'Restauracje i kawiarnie': 'Lukullus, Tawerna grecka - 400m, Pizzeria Bella - 900m'})])
def test_get_offer_apartment_details(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_apartment_details(
            BeautifulSoup(pickle.load(markup_file), "html.parser")) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [("test_data/offer", "516058058")])
def test_get_offer_phone_number(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_phone_number(
            BeautifulSoup(pickle.load(markup_file), "html.parser")) == expected_value


@pytest.mark.skipif(sys.version_info < (3, 1), reason="requires Python3")
@pytest.mark.parametrize('markup_path,expected_value', [("test_data/offer", "BIURO NIERUCHOMOŚCI ZALESKI")])
def test_get_offer_company_name(markup_path, expected_value):
    with open(markup_path, "rb") as markup_file:
        assert offer.get_offer_company_name(
            BeautifulSoup(pickle.load(markup_file), "html.parser")) == expected_value


@pytest.mark.parametrize("url,context", [
    (
        "https://www.gratka.pl/oferta/gdansk-apartament-olivaseaside-mieszkanie-na-doby-ID3iqMs.html",
        {
            'detail_url': 'https://www.gratka.pl/oferta/'
                          'gdansk-apartament-olivaseaside-mieszkanie-na-doby-ID3iqMs.html#a7099545ba',
            'offer_id': '3iqMs',
            'poster': 'Oferta prywatna'
        }
    )
])
def test_get_offer_information(url, context):
        with mock.patch("gratka.offer.get_response_for_url") as get_response_for_url,\
                mock.patch("gratka.offer.BeautifulSoup") as BeautifulSoup,\
                mock.patch("gratka.offer.get_offer_detail_jsons") as get_offer_detail_jsons, \
                mock.patch("gratka.offer.get_offer_apartment_details") as get_offer_apartment_details, \
                mock.patch("gratka.offer.get_offer_company_name") as get_offer_company_name, \
                mock.patch("gratka.offer.get_offer_phone_number") as get_offer_phone_number, \
                mock.patch("gratka.offer.get_offer_details") as get_offer_details, \
                mock.patch("gratka.offer.get_offer_photos_links") as get_offer_photos_links, \
                mock.patch("gratka.offer.get_offer_video_link") as get_offer_video_link:
            assert offer.get_offer_information(url, context)
            assert get_response_for_url.called
            assert BeautifulSoup.called
            assert get_offer_detail_jsons.called
            assert get_offer_apartment_details.called
            assert get_offer_company_name.called
            assert get_offer_phone_number.called
            assert get_offer_details.called
            assert get_offer_photos_links.called
            assert get_offer_video_link.called

