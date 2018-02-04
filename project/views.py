from project.mongo_db import Database


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
