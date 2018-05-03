import datetime

from apistar import Component
from apistar.http import Response
from apistar.types import Settings
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import ReturnDocument
from weather import Weather, Unit

from pprint import pprint as pp


def serialize_object_id(funk):
    """
    Decorator that first checks if connected to mongo, if not return 503 else transforms
    ObjectIds to str because json can NOT serialize ObjectIds,
    :param funk: the function to decorate
    :return: query with converted _id or 503 if no connection to mongo
    """

    def wrapper(self, *args, **kwargs):
        """python magic"""
        if not self.ping():
            return Response({'reason': 'Database is down'}, status=503)
        q = funk(self, *args, **kwargs)
        qq = []
        if isinstance(q, dict):
            q['_id'] = str(q['_id'])
            if q.get('rapporter'):
                q['rapporter'] = [str(i) for i in q['rapporter']]
        else:
            for doc in q:
                doc['_id'] = str(doc['_id'])
                if doc.get('scraped'):
                    doc['scraped'] = str(doc['scraped'])
                if doc.get('raw_html'):
                    del doc['raw_html']
                if doc.get('rapporter'):
                    doc['rapporter'] = [str(i) for i in doc['rapporter']]
                if doc.get('properties'):
                    doc['properties']['_id'] = str(doc['properties']['_id'])
        return q

    return wrapper


class Database(Component):
    """
    MongoDB class that holds all methods for interact with mongo.
    """

    def __init__(self, uri: str, db: str, uni_coll: str, country_coll: str, reports_coll: str,
                 users_coll: str) -> None:
        """
        Creates connections to the database
        :param uri:  Uri for mongodb e.g "mongodb://localhost:27017/gib"
        :param db: the database in mongodb, e.g. 'gib'
        :param uni_coll: the university collection in the database, e.g. 'uni'
        :param country_coll: the country collection in the database, e.g. 'world_countries'
        """
        super().__init__(Database)
        self._mongo = MongoClient(uri)
        self._db = self._mongo[db]
        self._uni = self._db[uni_coll]
        self._country = self._db[country_coll]
        self._reports = self._db[reports_coll]
        self._users = self._db[users_coll]
        self._cache = self._db['cache']

    def ping(self) -> bool:
        """
        Pings the database
        :return: Bool
        """
        try:
            self._db.command('ping')  # this method will timeout if no connection found
            return True
        except:
            return False

    @serialize_object_id
    def get_university_by_id(self, uni_id: str):
        """
        returns the university the _id match if found in database, else []
        :param uni_id: string, hex
        :return: dict
        """
        q = self._uni.find_one({'_id': ObjectId(uni_id)})
        q['rating'] = {
            'positive': 0,
            'negative': 0
        }
        reports = self.get_reports_for_university(uni_id)
        for report in reports:
            q['rating']['positive'] += 1 if report['Vil du anbefale andre å reise til studiestedet?'] == 'ja' else 0
            q['rating']['negative'] += 1 if report['Vil du anbefale andre å reise til studiestedet?'] == 'nei' else 0

        return q

    @serialize_object_id
    def get_university_geojson_by_id(self, uni_id) -> list:
        q = list(self._uni.aggregate([{'$match': {'_id': ObjectId(uni_id)}},
                                      {'$project': {
                                          'type': 'Feature',
                                          'properties.universitet': '$universitet',
                                          'properties._id': '$_id',
                                          'geometry': '$geometry'
                                      }}]))
        return q

    @serialize_object_id
    def list_all_uni(self) -> list:
        """
        returns queries with id and key e.g key=universitet
        :return:  Cursor
        """
        q = list(self._uni.aggregate([{'$match': {'_id': {'$exists': True}}},
                                      {
                                          '$project': {
                                              'type': 'Feature',
                                              'properties.university': '$universitet',
                                              'properties._id': '$_id',
                                              'properties.rapporter_antall': '$rapporter_antall',
                                              'geometry': '$geometry',
                                          }
                                      },
                                      {'$sort': {'properties.rapporter_antall': -1}}
                                      ]))
        return q

    @serialize_object_id
    def search_by_all(self, text: str) -> list:
        """
        Returns regex match on text in the database
        :param text: string of search
        :return: list of universities
        """

        def remove_reports(_q):
            if _q.get('rapporter'):
                del _q['rapporter']
            return _q

        q = [remove_reports(i) for i in self._uni.find({'geometry': {'$exists': 1}, '$text': {'$search': text}},
                                                       {'score': {'$meta': "textScore"}}
                                                       ).sort([('score', {'$meta': 'textScore'})])]
        return q

    @serialize_object_id
    def get_country_list(self, country):
        count = self._country.find_one({'properties.name': {'$regex': country, '$options': 'i'}},
                                       {'geometry': 1, '_id': 0})
        q = list(self._uni.find({'geometry': {'$geoWithin': {'$geometry': count['geometry']}}}))
        q = sorted(q, key=lambda x: x.get('rapporter_antall', -1), reverse=True)
        return q

    def get_fagomraader(self, search: str) -> list:
        q = self._uni.distinct('Fagområde')
        if search:
            q = [i for i in q if search.lower() in i.lower()]
        return q

    @serialize_object_id
    def get_reports_for_university(self, university_id: str) -> list:
        reports_ids = self._uni.find_one({'_id': ObjectId(university_id)},
                                         {'rapporter': 1, '_id': 0}).get('rapporter')
        if reports_ids:
            def fix_empty_strings(x):
                for k, v in x.items():
                    if not v:
                        x[k] = ''
                return x
            q = list(map(lambda x: fix_empty_strings(x), self._reports.find({'_id': {'$in': reports_ids}})))
        else:
            q = []
        return q

    def _get_reports_for_universities(self, university_ids) -> list:
        reports_ids = []
        for uni in self._uni.find({'_id': {'$in': university_ids}}, {'rapporter': 1, '_id': 0}):
            if uni.get('rapporter'):
                reports_ids += uni.get('rapporter')
        if reports_ids:
            q = list(self._reports.find({'_id': {'$in': reports_ids}}))
        else:
            q = []
        return q

    @serialize_object_id
    def search_universities(self, search: str):
        """
        Full text search on universities. Retrieves the top 6 results as geojson
        :param search: str
        :return: list of universities as geojson
        """
        def remove_reports(_q):
            if _q.get('rapporter'):
                del _q['rapporter']
            _q['_id'] = str(_q['_id'])
            del _q['raw_html']
            return _q

        q = list(self._uni.aggregate([{'$match': {'geometry': {'$exists': 1}, '$or': [{'universitet': {'$regex': search, '$options': 'i'}}, {'land': {'$regex': search, '$options': 'i'}}, {'by': {'$regex': search, '$options': 'i'}}]}},
                                      {'$project': {
                                          'type': 'Feature',
                                          'properties.university': '$universitet',
                                          'properties._id': '$_id',
                                          'geometry': '$geometry'
                                      }}
                                      ]))[:6]
        return q

    def _add_star_to_university(self, uni_id):
        """increment the star value of a university"""
        self._uni.update_one({'_id': ObjectId(uni_id)}, {'$inc': {'star_count': 1}})

    def get_or_create_user(self, email: str):
        # user exists
        user = self._users.find_one({'_id': email})
        # validation
        if not email.endswith('@stud.ntnu.no'):
            return {'message': f'{email}: invalid username'}
        # create user
        if not user:
            user = self._users.find_one_and_update(
                {'_id': email},
                {
                    '$set':
                        {
                           'last_modified': datetime.datetime.utcnow().isoformat(),
                           'my_universities': {}
                        }
                },
                upsert=True,
                return_document=ReturnDocument.AFTER)
        uni_ids = user['my_universities'].keys()
        unis = [self.get_university_by_id(uni) for uni in uni_ids]
        for uni in unis:
            uni['_id'] = str(uni['_id'])
            if uni.get('rapporter'):
                del uni['rapporter']
            del uni['raw_html']
            user['my_universities'][uni.get('_id')]['university'] = uni

        for uni_id in user['my_universities'].keys():
            user['my_universities'][uni_id]['notes'] = list(user['my_universities'][uni_id]['notes'].items())
            user['my_universities'][uni_id]['links'] = list(user['my_universities'][uni_id]['links'].items())
        user['my_universities'] = list(user['my_universities'].values())

        return user

    def add_uni_to_cart(self, email: str, uni_id: str):
        user = self._users.find_one({'_id': email}, {'my_universities': 1})
        # no user by that id
        if not user:
            return 'user not found'
        # no id found
        if uni_id not in [str(i.get('_id')) for i in self._uni.find({}, {'_id': 1})]:
            return 'university_id not found'
        # if already added
        if uni_id in user['my_universities'].keys():
            return 'university already added'

        self._users.update_one({'_id': email},
                               {'$set': {
                                   'last_modified': datetime.datetime.utcnow().isoformat(),
                                   f'my_universities.{uni_id}.notes': {},
                                   f'my_universities.{uni_id}.links': {}
                               }}
                               )
        self._add_star_to_university(uni_id)
        user = self.get_or_create_user(email)
        return user

    def remove_uni_from_cart(self, email: str, uni_id: str):
        user = self._users.update_one({'_id': email,
                                       f'my_universities.{uni_id}': {'$exists': True}},
                                      {'$unset': {f'my_universities.{uni_id}': True},
                                       '$set': {
                                           'last_modified': datetime.datetime.utcnow().isoformat(),
                                       }
                                       })
        user = self.get_or_create_user(email)
        return user

    def add_link_or_note(self, email, uni_id, head, note, link):
        user = self._users.find_one({'_id': email}, {'my_universities': 1})
        # no user by that id
        if not user:
            return 'user not found'
        # my_uni_id not found
        if not user['my_universities'].get(uni_id):
            return 'uni_id not found'
        to_update = 'notes' if note else 'links'
        to_update_key = 'note' if note else 'link'
        to_update_value = note if note else link
        try:
            next_id = max([int(i) for i in user['my_universities'].get(uni_id).get(
                to_update).keys()]) + 1
        except:
            next_id = 0
        self._users.update_one({'_id': email},
                               {
                                   '$set': {
                                       f'my_universities.{uni_id}.{to_update}.{next_id}':
                                           {'head': head,
                                            f'{to_update_key}': to_update_value},
                                       'last_modified': datetime.datetime.utcnow().isoformat()
                                   }
                                })
        return 'ok'

    def remove_link_or_note(self, email, uni_id, note_id, link_id):
        user = self._users.find_one({'_id': email}, {'my_universities': 1})
        # no user by that id
        if not user:
            return 'user not found'
        # my_uni_id not found
        if not user['my_universities'].get(uni_id):
            return 'uni_id not found'
        to_update_id = note_id if note_id else link_id
        to_update = 'notes' if note_id else 'links'
        self._users.update_one({'_id': email},
                               {
                                   '$unset': {
                                       f'my_universities.{uni_id}.{to_update}.{to_update_id}': True
                                   },
                                   '$set': {
                                       'last_modified': datetime.datetime.utcnow().isoformat(),
                                   }
                               })
        return 'ok'

    def get_university_and_score(self):
        university_and_score = list(self._uni.find({'rapporter_antall': {'$exists': True}},
                                                   {
                                                       '_id': 0,
                                                       'rapporter_antall': 1,
                                                       'universitet': 1
                                                   }))
        return university_and_score

    def _list_all_country_names_with_geo(self):
        # TODO smarter queries
        countries = self._country.find({}, {'properties.name': 1, '_id': 0, 'geometry': 1})
        return countries
    
    def get_choropleth_countries(self):
        choropleth = self._cache.find_one({'_id': 'get_choropleth_countries'})
        if not choropleth:
            countries = self._list_all_country_names_with_geo()
            total_reports_count = self._reports.find().count()
            total_uni_count = self._uni.find().count()

            report_total = 0
            # report_count = 0
            university_total = 0
            # university_count = 0

            choropleth = {
                'type': 'FeatureCollection',
                'features': []
            }
            for country in countries:
                country_with_unis = self.get_country_list(country['properties']['name'])
                country['type'] = 'Feature'
                country['properties'] = {
                    'name': country['properties']['name']
                }
                if not country_with_unis:
                    country['properties']['report_rating'] = 0
                    country['properties']['university_rating'] = 0
                    country['properties']['social_rating'] = 0
                    country['properties']['academic_rating'] = 0
                    choropleth['features'].append(country)
                    continue
                # del country['geometry']

                unis_in_country_count = len(country_with_unis)
                unis_in_country = [uni['_id'] for uni in country_with_unis]
                university_rating = unis_in_country_count / total_uni_count

                reports_in_country = self._get_reports_for_universities([ObjectId(i) for i in unis_in_country])
                reports_in_country_count = len(reports_in_country)
                reports_in_country_rating = reports_in_country_count / total_reports_count
                # pp([int(r['Hvordan vil du rangere den sosiale opplevelsen?']) for r in reports_in_country])
                # pp(reports_in_country)
                social_in_country_rating = (sum([int(r['Hvordan vil du rangere den sosiale opplevelsen?']) for r in reports_in_country]) \
                                                / reports_in_country_count) if reports_in_country_count else 0
                academic_in_country_rating = (sum([int(r['Hvordan vil du rangere den akademiske kvaliteten?']) for r in reports_in_country]) \
                                                / reports_in_country_count) if reports_in_country_count else 0

                # social_rating = sum([uni for uni in country_with_unis['features']['properties']])
                country['properties']['report_rating'] = reports_in_country_rating
                report_total += reports_in_country_rating
                # report_count += 1
                country['properties']['university_rating'] = university_rating
                university_total += university_rating
                # university_count += 1
                country['properties']['social_rating'] = social_in_country_rating
                country['properties']['academic_rating'] = academic_in_country_rating
                choropleth['features'].append(country)

            for c in choropleth['features']:
                c['properties']['report_rating'] /= report_total
                c['properties']['university_rating'] /= university_total
            choropleth['_id'] = 'get_choropleth_countries'
            self._cache.insert_one(dict(choropleth))
        else:
            del choropleth['_id']
        report_rating = sorted(filter(lambda x: x['properties']['report_rating'] != 0, choropleth['features']), key=lambda x: x['properties']['report_rating'])
        report_rating_step = len(report_rating) // 4
        report_rating_groups = [report_rating[i]['properties']['report_rating'] for i in range(report_rating_step, len(report_rating), report_rating_step)]
        report_rating_groups.insert(0, 0)

        university_rating = sorted(filter(lambda x: x['properties']['university_rating'] != 0, choropleth['features']), key=lambda x: x['properties']['university_rating'])
        university_rating_step = len(university_rating) // 4
        university_rating_groups = [university_rating[i]['properties']['university_rating'] for i in range(university_rating_step, len(university_rating), university_rating_step)]
        university_rating_groups.insert(0, 0)

        choropleth['university_rating_groups'] = university_rating_groups
        choropleth['report_rating_groups'] = report_rating_groups

        return choropleth

    def get_money_for_uni(self, uni_id):
        """
        Returns money stats for every university if uni_id is None
        if uni_id is provided only return money stats for that uni
        """

        def fix_money(money):
            try:
                return int(''.join(money.replace('kr', '').replace('_', '').strip().split()))
            except:
                return

        if uni_id:
            unis = [self._uni.find_one({'_id': ObjectId(uni_id)}, {'rapporter': 1, 'universitet': 1})]
            money_stats = False
        else:
            money_stats = self._cache.find_one({'_id': 'money_stats'})
            if not money_stats:
                unis = list(self._uni.find({'rapporter': {'$exists': 1}}, {'rapporter': 1, 'universitet': 1}))
            else:
                return money_stats['unis']
        if not money_stats:
            for uni in unis:
                uni['_id'] = str(uni['_id'])
                uni['money_stats'] = {
                    'skolepenger': 0,
                    'skolepenger_liste': [],
                    'boligutgifter': 0,
                    'boligutgifter_liste': [],
                    'ekstra': 0,
                    'ekstra_liste': [],
                }
                reports = self.get_reports_for_university(uni['_id']) if uni.get('rapporter') else []
                if reports:
                    del uni['rapporter']
                for report in reports:
                    skolepenger = fix_money(report['Hva var skolepengene pr_ semester?'])
                    if skolepenger and 300000 > skolepenger is not None:
                        uni['money_stats']['skolepenger_liste'].append(skolepenger)
                        uni['money_stats']['skolepenger'] += skolepenger
                    boligutgifter = fix_money(report['Hva var boligutgiftene pr_ måned (inkludert strøm, internett osv_)?'])
                    if boligutgifter and 15001 > boligutgifter is not None:
                        uni['money_stats']['boligutgifter_liste'].append(boligutgifter)
                        uni['money_stats']['boligutgifter'] += boligutgifter
                    ekstra = fix_money(report['Hvor mye brukte du i tillegg til pengene fra Lånekassen i løpet av oppholdet?'])
                    if ekstra and 500000 > ekstra is not None:
                        uni['money_stats']['ekstra_liste'].append(ekstra)
                        uni['money_stats']['ekstra'] += ekstra
                uni['money_stats']['skolepenger'] = uni['money_stats']['skolepenger'] // len(uni['money_stats']['skolepenger_liste']) if uni['money_stats']['skolepenger_liste'] else None
                uni['money_stats']['boligutgifter'] = uni['money_stats']['boligutgifter'] // len(uni['money_stats']['boligutgifter_liste']) if uni['money_stats']['boligutgifter_liste'] else None
                uni['money_stats']['ekstra'] = uni['money_stats']['ekstra'] // len(uni['money_stats']['ekstra_liste']) if uni['money_stats']['ekstra_liste'] else None
            if not uni_id and not money_stats:
                money_stats = {
                    '_id': 'money_stats',
                    'unis': unis,
                }
                pp(money_stats)
                self._cache.insert_one(dict(money_stats))
        return unis

    @serialize_object_id
    def get_top_stared_universities(self):
        """Returns the top 4 universities based on star_count"""
        unis = self._uni.find({'star_count': {'$exists': 1}})
        top4 = sorted(unis, key=lambda x: -x['star_count'])[:4]
        return top4

    def _set_distance_from_ntnu_to_uni(self):
        """adds distance to NTNU for every university"""
        a = list(self._uni.aggregate(
            [
                {
                    "$geoNear":
                    {
                        "near":
                        {
                            "type": "Point",
                            "coordinates": [10.402077, 63.419499]
                        },
                        "num": 1000,
                        "spherical": True,
                        "maxDistance": 10000000000,
                        "distanceField": "distance",
                    }
                }
            ]))
        for uni in a:
            self._uni.update_one({'_id': uni['_id']}, {'$set': {'meters_from_ntnu': uni['distance']}})
    
    def update_weather(self):
        """
        Updates weather today for every university
        can only run once a day
        """
        # self._cache.update_one({'_id': 'weather_date'}, {'$set': {'date': datetime.datetime.today()}})
        last_run = self._cache.find_one({'_id': 'weather_date'})
        if last_run['date'] < datetime.datetime.today():
            weather = Weather(unit=Unit.CELSIUS)
            for uni in list(self._uni.find({'geometry': {'$exists': 1}})):
                long, lat = uni['geometry']['coordinates']
                location = weather.lookup_by_latlng(lat, long)
                self._uni.update_one({'_id': uni['_id']}, {'$set': {'weather': {'min': int(location.forecast[0].low), 'high': int(location.forecast[0].high)}}})
            self._cache.update_one({'_id': 'weather_date'}, {'$set': {'date': datetime.datetime.today() + datetime.timedelta(days=1)}})
            return 'updated'
        else:
            return 'wait to update'

def init_database(settings: Settings):
    # TODO
    return Database(settings['MONGO_URI'], settings['MONGO_DB'], settings['MONGO_UNI_COLL'],
                    settings['MONGO_COUNTRY_COLL'], settings['MONGO_REPORTS_COLL'],
                    settings['MONGO_USERS_COLL'])

