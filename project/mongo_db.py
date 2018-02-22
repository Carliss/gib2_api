from apistar import Component
from apistar.http import Response
from apistar.types import Settings
from bson import ObjectId
from pymongo import MongoClient


class Database(Component):
    """
    MongoDB class that holds all methods for interact with mongo.
    """

    def __init__(self, uri: str, db: str, uni_coll: str, country_coll: str) -> None:
        """
        Creates connections to the database
        :param uri:  Uri for mongodb e.g "mongodb://localhost:27017/gib"
        :param db: the database in mongodb, e.g. 'gib'
        :param uni_coll: the university collection in the database, e.g. 'uni'
        :param country_coll: the country collection in the database, e.g. 'world_countries'
        """
        self._mongo = MongoClient(uri)
        self._db = self._mongo[db]
        self._uni_coll = self._db[uni_coll]
        self._country_coll = self._db[country_coll]

    def _serialize_object_id(funk):
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
            for doc in q:
                doc['_id'] = str(doc['_id'])
            return q
        return wrapper

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

    def get_university_by_id(self, _id: str):
        """
        returns the university the _id match if found in database, else []
        :param _id: string, hex
        :return: dict
        """
        q = self._uni_coll.find_one({'_id': ObjectId(_id)})
        q['_id'] = str(q['_id'])
        return q

    @_serialize_object_id
    def list_all_uni(self) -> list:
        """
        returns queries with id and key e.g key=universitet
        :param key: mongodb field name
        :return:  Cursor
        """
        q = list(self._uni_coll.aggregate([{'$match': {'_id': {'$exists': True}}},
                                          {'$project': {
                                              'type': 'Feature',
                                              'properties.university': '$universitet',
                                              'properties._id': '$_id',
                                              'geometry': '$geometry'
                                          }}]))
        return q

    @_serialize_object_id
    def search_by_all(self, text: str) -> list:
        """
        Returns regex match on text in the database
        :param text: string of search
        :return: list of universities
        """
        q = list(self._uni_coll.find({'$text': {'$search': text}},
                                     {'score': { '$meta': "textScore" }}
                                     ))
        return q

    @_serialize_object_id
    def get_country_list(self, country):
        # TODO
        count = self._country_coll.find_one({'properties.name': {'$regex': country,
                                                                 '$options': 'i'
                                                                 }},
                                            {'geometry': 1, '_id': 0})
        print(count)
        q = list(self._uni_coll.find({'geometry': { '$geoWithin': { '$geometry' : count[
            'geometry']}}}))
        print(q)

        return q

    @_serialize_object_id
    def get_fagomraader(self, search: str=None) -> list:
        # TODO
        q = self._uni_coll.distinct('Fagområde')
        return q


def init_database(settings: Settings):
    # TODO
    return Database(settings['MONGO_URI'], settings['MONGO_DB'], settings['MONGO_UNI_COLL'],
                    settings['MONGO_COUNTRY_COLL'])
