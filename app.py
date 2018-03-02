from apistar.frameworks.wsgi import WSGIApp as App
from apistar import Component

from project.routes import routes
from project.mongo_db import Database, init_database


settings = {
    # 'MONGO_URI': 'mongodb://localhost:27017/',
    "MONGO_URI": 'mongodb://gib_dude:Gibbing2018@ds125368.mlab.com:25368/gib',
    'MONGO_DB': 'gib',
    'MONGO_UNI_COLL': 'uni',
    'MONGO_COUNTRY_COLL': 'world_countries',
    'MONGO_REPORTS_COLL': 'rapporter'
}


components = [
    Component(Database, init=init_database, preload=True),
]


app = App(
    settings=settings,
    routes=routes,
    components=components
    )


if __name__ == '__main__':
    app.main()
