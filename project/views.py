from project.mongo_db import Database
from apistar.http import Response

def welcome():
    return {'Welcome': 'Hello world'}


def mongo_ok(db: Database):
    if db.ping():
        return {'status': 'OK'}
    return {'status': 'NOT OK'}


def list_all_uni(key, db: Database):
    q = db.list_all_uni(key)
    return q


def get_all_uni(db: Database):
    q = db.get_all_uni()
    return q


def search_by_all(db: Database, text):
    q = db.search_by_all(text)
    return q


def uni_in_country(db: Database, country):
    q = db.get_country_list(country)
    if not q:
        return {'error': 'no country found'}
    qq = []
    for i in q:
        ii = {"type": "Feature",
      "properties": {"scalerank": 1,
        "featurecla": "Admin-0 country",
        "labelrank": 6,
        "sovereignt": "Belize",
        "sov_a3": "BLZ",
        "adm0_dif": 0,
        "level": 2,
        "type": "Sovereign country",
        "admin": "Belize",
        "adm0_a3": "BLZ",
        "geou_dif": 0,
        "geounit": "Belize",
        "gu_a3": "BLZ",
        "su_dif": 0,
        "subunit": "Belize",
        "su_a3": "BLZ",
        "brk_diff": 0,
        "name": "Belize",
        "name_long": "Belize",
        "brk_a3": "BLZ",
        "brk_name": "Belize",
        "brk_group": None,
        "abbrev": "Belize",
        "postal": "BZ",
        "formal_en": "Belize",
        "formal_fr": None,
        "note_adm0": None,
        "note_brk": None,
        "name_sort": "Belize",
        "name_alt": None,
        "mapcolor7": 1,
        "mapcolor8": 4,
        "mapcolor9": 5,
        "mapcolor13": 7,
        "pop_est": 307899,
        "gdp_md_est": 2536,
        "pop_year": -99,
        "lastcensus": 2010,
        "gdp_year": -99,
        "economy": "6. Developing region",
        "income_grp": "4. Lower middle income",
        "wikipedia": -99,
        "fips_10": None,
        "iso_a2": "BZ",
        "iso_a3": "BLZ",
        "iso_n3": "084",
        "un_a3": "084",
        "wb_a2": "BZ",
        "wb_a3": "BLZ",
        "woe_id": -99,
        "adm0_a3_is": "BLZ",
        "adm0_a3_us": "BLZ",
        "adm0_a3_un": -99,
        "adm0_a3_wb": -99,
        "continent": "North America",
        "region_un": "Americas",
        "subregion": "Central America",
        "region_wb": "Latin America & Caribbean",
        "name_len": 6,
        "long_len": 6,
        "abbrev_len": 6,
        "tiny": -99,
        "homepart": 1,
        "filename": "BLZ.geojson"}}
        ii['geometry'] = i['location']
        qq.append(ii)
    return Response({
        "type": "FeatureCollection",
        "features":qq
    },
        headers={"Access-Control-Allow-Origin": '*'}
    )