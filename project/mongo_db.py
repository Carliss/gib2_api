from apistar import Component
from pymongo import MongoClient, DESCENDING
# from bson import ObjectId
from apistar.types import Settings
from apistar.http import Response


class Database(Component):
    """
    MongoDB class that holds all methods for interact with mongo.
    """

    def __init__(self, uri, db, coll):
        """
        :param uri:  Uri for mongodb e.g "mongodb://localhost:27017/gib"
        :param db: the database in mongodb
        :param coll: the collection in the database
        """
        self._mongo = MongoClient(uri)
        self._db = self._mongo[db]
        self._coll = self._db[coll]

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

    def ping(self):
        """
        test if the app has connection to mongo
        :return: Bool
        """
        ping = False
        try:
            self._db.command('ping')
            ping = True
        except:
            pass
        return ping

    @_serialize_object_id
    def get_all_uni(self):
        """
        returns every uni doc in the collection
        :return: list with uni docs
        """
        q = list(self._coll.find({}))
        return q

    @_serialize_object_id
    def list_all_uni(self, key):
        """
        returns queries with id and key e.g key=universitet
        :param key: mongodb field name
        :return:  list of queries with key
        """
        q = list(self._coll.find({}, {key: 1}))
        return q

    @_serialize_object_id
    def search_by_all(self, text):
        q = list(self._coll.find({'$text': {'$search': text}},
                                 {'score': { '$meta': "textScore" }}
                                 ))
        return q


def init_database(settings: Settings):
    # TODO
    return Database(settings['MONGO_URI'], settings['MONGO_DB'], settings['MONGO_COLL'])
