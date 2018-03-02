from apistar.http import Response, QueryParams

from project.mongo_db import Database


# --------- Important -------------
# if the api is called from the same domain, we need to set Access-Control-Allow-Origin to *


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
        data = {'status': 'OK'}
    else:
        data = {'status': 'NOT OK'}
    return Response(data, headers={"Access-Control-Allow-Origin": '*'})


def list_all_uni_as_geo_json(db: Database):
    q = db.list_all_uni()
    return Response(as_geojson(q), headers={"Access-Control-Allow-Origin": '*'})


def search_by_all(db: Database, text):
    q = db.search_by_all(text.encode('latin-1').decode('utf-8'))
    return Response(q, headers={"Access-Control-Allow-Origin": '*'})


def uni_in_country(db: Database, country):
    q = db.get_country_list(country.encode('latin-1').decode('utf-8'))
    if not q:
        return {'error': 'no country found'}
    qq = []
    for i in q:
        ii = {
            "type": "Feature",
            "properties": i,
            'geometry': i['geometry']
        }
        qq.append(ii)
    return Response({
        "type": "FeatureCollection",
        "features": qq
    }, headers={"Access-Control-Allow-Origin": '*'})


def get_fagomraader(db: Database, search: str):
    search = (search.encode('latin-1').decode('utf-8'))
    q = db.get_fagomraader(search if search != 'all' else None)
    return Response(q, headers={"Access-Control-Allow-Origin": '*'})


def get_reports_for_university(db: Database, _id: str):
    q = db.get_reports_for_university(_id)
    return Response(q, headers={"Access-Control-Allow-Origin": '*'})


def advanced_search(params: QueryParams):
    """
    TODO
    :param params:
        :params fagområde:
        :params land:
        :params by:
        :params :
    :return:
    """
    return params.keys()


def create_or_get_user(db: Database, email: str):
    user = db.get_or_create_user(email)
    return Response(user, headers={"Access-Control-Allow-Origin": '*'})


def add_uni_to_cart(db: Database, email: str, uni_id: str):
    message = db.add_uni_to_cart(email, uni_id)
    data = {'message': message}
    return Response(data, headers={"Access-Control-Allow-Origin": '*'})


def remove_uni_from_cart(db: Database, email: str, uni_id: str):
    message = db.remove_uni_from_cart(email, uni_id)
    data = {'message': message}
    return Response(data, headers={"Access-Control-Allow-Origin": '*'})


def add_link_or_note(db: Database, qp: QueryParams, email: str):
    uni_id = qp.get('uni_id')
    head = qp.get('head')
    note = qp.get('note')
    link = qp.get('link')
    message = db.add_link_or_note(email, uni_id, head, note, link)
    return Response({'message': message}, headers={"Access-Control-Allow-Origin": '*'})


def remove_link_or_note(db: Database, qp: QueryParams, email: str):
    uni_id = qp.get('uni_id')
    note_id = qp.get('note_id')
    link_id = qp.get('link_id')
    message = db.remove_link_or_note(email, uni_id, note_id, link_id)
    return Response({'message': message}, headers={"Access-Control-Allow-Origin": '*'})
