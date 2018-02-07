from apistar import Route, Include
from apistar.handlers import docs_urls, static_urls

from project import views

routes = [
    # Route('/', 'GET', views.welcome),

    Route('/mongo_ok', 'GET', views.mongo_ok),

    Route('/uni/{key}', 'GET', views.list_all_uni),

    Route('/uni/all', 'GET', views.get_all_uni),

    Route('/search_by_all/{text}', 'GET', views.search_by_all),

    Route('/uni_in_country/{country}', 'GET', views.uni_in_country),

    Include('/', docs_urls),
    Include('/static', static_urls)
]
