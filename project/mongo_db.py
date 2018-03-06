import datetime

from apistar import Component
from apistar.http import Response
from apistar.types import Settings
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import ReturnDocument

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
    def get_university_by_id(self, _id: str):
        """
        returns the university the _id match if found in database, else []
        :param _id: string, hex
        :return: dict
        """
        q = self._uni.find_one({'_id': ObjectId(_id)})

        return q

    @serialize_object_id
    def list_all_uni(self) -> list:
        """
        returns queries with id and key e.g key=universitet
        :return:  Cursor
        """
        q = list(self._uni.aggregate([{'$match': {'_id': {'$exists': True}}},
                                      {'$project': {
                                          'type': 'Feature',
                                          'properties.university': '$universitet',
                                          'properties._id': '$_id',
                                          'geometry': '$geometry'
                                      }}]))
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

        q = [remove_reports(i) for i in self._uni.find({'$text': {'$search': text}},
                                                       {'score': {'$meta': "textScore"}}
                                                       ).sort([('score', {'$meta': 'textScore'})])]
        return q

    @serialize_object_id
    def get_country_list(self, country):
        count = self._country.find_one({'properties.name': {'$regex': country, '$options': 'i'}},
                                       {'geometry': 1, '_id': 0})
        q = list(self._uni.find({'geometry': {'$geoWithin': {'$geometry': count['geometry']}}}))

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
            q = list(self._reports.find({'_id': {'$in': reports_ids}}))
        else:
            q = []
        return q

    @serialize_object_id
    def search_universities(self, search: str):
        def remove_reports(_q):
            if _q.get('rapporter'):
                del _q['rapporter']
            _q['_id'] = str(_q['_id'])
            del _q['raw_html']
            return _q

        # q = [remove_reports(i) for i in self._uni.find({'$text': {'$search': search}},
        #                                                {'score': {'$meta': "textScore"}}
        #                                                ).sort([('score',
        #                                                         {'$meta': 'textScore'})]
        #                                                       )[:5]]
        q = list(self._uni.aggregate([{'$match': {'$text': {'$search': search}}},
                                      {'$sort': {'score': {'$meta': 'textScore'}}},
                                      {'$project': {
                                          'type': 'Feature',
                                          'properties.university': '$universitet',
                                          'properties._id': '$_id',
                                          'geometry': '$geometry'
                                      }}
                                      ]))
        return q

    def get_or_create_user(self, email: str):
        # todo add validation
        # user exists
        user = self._users.find_one({'_id': email})
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
        unis = list(self._uni.find({'_id': {'$in': [ObjectId(i) for i in uni_ids]}}))
        for uni in unis:
            uni['_id'] = str(uni['_id'])
            if uni.get('rapporter'):
                del uni['rapporter']
            del uni['raw_html']
            user['my_universities'][uni.get('_id')]['university'] = uni

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
        return 'ok'

    def remove_uni_from_cart(self, email: str, uni_id: str):
        user = self._users.update_one({'_id': email,
                                       f'my_universities.{uni_id}': {'$exists': True}},
                                      {'$unset': {f'my_universities.{uni_id}': True},
                                       '$set': {
                                           'last_modified': datetime.datetime.utcnow().isoformat(),
                                       }
                                       })
        return 'ok' if user.modified_count else 'nothing updated'

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


def init_database(settings: Settings):
    # TODO
    return Database(settings['MONGO_URI'], settings['MONGO_DB'], settings['MONGO_UNI_COLL'],
                    settings['MONGO_COUNTRY_COLL'], settings['MONGO_REPORTS_COLL'],
                    settings['MONGO_USERS_COLL'])
