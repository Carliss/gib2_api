from functools import wraps

from apistar.http import Response, QueryParams

from project.mongo_db import Database


LOCALHOST = True


def allow_cross_origin(func):
    """
    Decorator to allow cross origin for testing on localhost
    allows cross origin if localhost is sat to True in app.settings
    :param func: the view function to be called
    :return: Response
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = func(*args, **kwargs)
        return Response(data, headers={"Access-Control-Allow-Origin": '*'}
                        ) if LOCALHOST else data
    return wrapper


def as_geojson(func):
    """
    Decorator that maps the data to GeoJson with FeaturedCollection
    :param func: the view function to be called
    :return: GeoJson
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = func(*args, **kwargs)
        if isinstance(data, list):
            for i in data:
                i['properties']['_id'] = str(i['properties']['_id'])
        return {
            'type': 'FeatureCollection',
            'features': data
        }
    return wrapper


@allow_cross_origin
def get_university_by_id(db: Database, _id: str):
    """
    Returns a geojson of the university that matched the _id
    :param db: Server side parameter
    :param _id: str of university id
    :return: GeoJson of the university
    """
    q = db.get_university_by_id(_id)
    return q


@allow_cross_origin
@as_geojson
def get_university_geojson_by_id(db: Database, uni_id: str):
    """
    Returns a geojson of the university that matched the _id
    :param db: Server side parameter
    :param _id: str of university id
    :return: GeoJson of the university
    """
    q = db.get_university_geojson_by_id(uni_id)
    return q


@allow_cross_origin
def ping_database(db: Database):
    """
    Used to test connection to MongoDB
    :param db: Server side parameter
    :return: json of status: OK/NOT OK
    """
    if db.ping():
        data = {'status': 'OK'}
    else:
        data = {'status': 'NOT OK'}
    return data


@allow_cross_origin
@as_geojson
def list_all_uni_as_geo_json(db: Database):
    """
    :param db: Server side parameter
    :return: GeoJson with every universities
    """
    q = db.list_all_uni()
    return q


@allow_cross_origin
def search_by_all(db: Database, text):
    """
    Full text search in "land", "by" and "universitet" in mongo,
    returns GeoJson of universities sorted by textScore
    :param db: Server side parameter
    :param text: str of search
    :return: GeoJson with every universities
    """
    q = db.search_by_all(text.encode('latin-1').decode('utf-8'))
    return q


@allow_cross_origin
@as_geojson
def uni_in_country(db: Database, country):
    """
    Returns the universities from county.
    Finds the best match for country by regex.
    :param db: Server side parameter
    :param country: str of country
    :return: GeoJson of universities in country
    """
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
    return qq


@allow_cross_origin
def get_fagomraader(db: Database, search: str):
    """
    if search is egual to "all" return all fagomraader,
    else return list of fagomraade that matched search by regex
    :param db: Server side parameter
    :param search: str of fagomraade, "all" returns everything
    :return: List of fagomraader
    """
    search = (search.encode('latin-1').decode('utf-8'))
    q = db.get_fagomraader(search if search != 'all' else None)
    return q


@allow_cross_origin
def get_reports_for_university(db: Database, _id: str):
    """
    Matched _id to university and returns the reports (if any)
    :param db: Server side parameter
    :param _id: str of university id
    :return: list of reports if university have reports else empty list
    """
    q = db.get_reports_for_university(_id)
    return q


@allow_cross_origin
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


@allow_cross_origin
@as_geojson
def search_universities(db: Database, search: str):
    """
    Used for search completion,
    Uses full text search to match the search, then return the
    top five result.
    :param db: Server side parameter
    :param search: str of search (country, city or university)
    :return: List of universities
    """
    q = db.search_universities(search)
    return q


@allow_cross_origin
def create_or_get_user(db: Database, email: str):
    """
    Finds or create user bby email, and returns the user
    :param db: Server side parameter
    :param email: str must end with stud.ntnu.no
    :return: user
    """
    user = db.get_or_create_user(email)
    return user


@allow_cross_origin
def add_uni_to_cart(db: Database, email: str, uni_id: str):
    """
    Add the university to the user
    :param db: Server side parameter
    :param email: str
    :param uni_id: str of the university id
    :return: updated user
    """
    user = db.add_uni_to_cart(email, uni_id)
    return user


@allow_cross_origin
def remove_uni_from_cart(db: Database, email: str, uni_id: str):
    """
    Removes the university from user
    :param db: Server side parameter
    :param email: str
    :param uni_id: str of university id
    :return: updated user
    """
    user = db.remove_uni_from_cart(email, uni_id)
    return user


@allow_cross_origin
def add_link_or_note(db: Database, qp: QueryParams, email: str):
    """
    Add link or note to user
    E.g: /add_link_or_note/test@stud.ntnu.no?uni_id=12345678&head=test&note=test
    NOTE: note or link must be defined
    :param db: add_link_or_note
    :param qp: params to the request
        :qp uni_id: str of university id
        :qp head: str of title of note/link
        :qp note: str
        :qp link: str
    :param email: str
    :return: message
    """
    uni_id = qp.get('uni_id')
    head = qp.get('head')
    note = qp.get('note')
    link = qp.get('link')
    message = db.add_link_or_note(email, uni_id, head, note, link)
    return {'message': message}


@allow_cross_origin
def remove_link_or_note(db: Database, qp: QueryParams, email: str):
    """
    Removes the link or note by note_id or link_id
    :param db: add_link_or_note
    :param qp: params to the request
        :qp uni_id: str of university id
        :qp note_id: str
        :qp link_id: str
    :param email: str
    :return: message
    """
    uni_id = qp.get('uni_id')
    note_id = qp.get('note_id')
    link_id = qp.get('link_id')
    message = db.remove_link_or_note(email, uni_id, note_id, link_id)
    return {'message': message}


@allow_cross_origin
def get_university_and_score(db: Database):
    """
    Returns a list of every university with at least one repport,
    on the form
    [
        {'universitet': str, 'rapport_antall': int},
        ...
    ]
    """
    universities_and_score = db.get_university_and_score()
    return universities_and_score


@allow_cross_origin
def get_choropleth_countries(db: Database):
    """
    Returns a list of countries in geojson with different stats to
    create choropleth maps on:
    - reports
    """
    countries = db.get_choropleth_countries()
    return countries
