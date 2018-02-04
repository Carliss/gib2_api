from apistar.frameworks.wsgi import WSGIApp as App
from apistar import Component

from project.routes import routes
from project.mongo_db import Database, init_database


settings = {
    'MONGO_URI': 'mongodb://localhost:27017/',
    'MONGO_DB': 'gib',
    'MONGO_COLL': 'uni'
}


components = [
    Component(Database, init=init_database, preload=True)
]


app = App(
    settings=settings,
    routes=routes,
    components=components
    )


if __name__ == '__main__':
    app.main()
