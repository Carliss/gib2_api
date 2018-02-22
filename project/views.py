from project.mongo_db import Database
from apistar.http import Response


def allow_cross_origin(func):
    def wrapper(*args, **kwargs):
        data = func(*args, **kwargs)
        return Response(data, headers={"Access-Control-Allow-Origin": '*'})
    return wrapper


def as_geojson(data):
    for i in data:
        i['properties']['_id'] = str(i['properties']['_id'])
    return {
        'type': 'FeatureCollection',
        'features': data
    }


def get_university_by_id(db: Database, _id: str):
    q = db.get_university_by_id(_id)
    return Response(q, headers={"Access-Control-Allow-Origin": '*'})


def ping_database(db: Database):
    if db.ping():
        return {'status': 'OK'}
    return {'status': 'NOT OK'}


def list_all_uni_as_geo_json(db: Database):
    q = db.list_all_uni()
    return Response(as_geojson(q),headers={"Access-Control-Allow-Origin": '*'}
    )


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
      "properties": i}
        ii['geometry'] = i['geometry']
        qq.append(ii)
    return Response({
        "type": "FeatureCollection",
        "features":qq
    },
        headers={"Access-Control-Allow-Origin": '*'}
    )


@allow_cross_origin
def get_fagomraader(db: Database, search=None):
    q = db.get_fagomraader()
    return q