from apistar import Route, Include
from apistar.handlers import docs_urls, static_urls

from project import views

routes = [
    Route('/ping_database', 'GET', views.ping_database, name='ping'),

    Route('/get_university_by_id/{_id}', 'GET', views.get_university_by_id),

    Route('/get_university_geojson_by_id/{uni_id}', 'GET', views.get_university_geojson_by_id,
          name="get_university_geojson_by_id"),

    Route('/list_all_uni_as_geo_json', 'GET', views.list_all_uni_as_geo_json,
          name='list_all_uni_as_geo_json'),

    Route('/search_by_all/{text}', 'GET', views.search_by_all),

    Route('/uni_in_country/{country}', 'GET', views.uni_in_country),

    Route('/get_fagomraader/{search}', 'GET', views.get_fagomraader,
          name='get_fagomraader'),

    Route('/advanced_search', 'GET', views.advanced_search, name='advanced_search'),

    Route('/get_reports_for_university/{_id}', 'GET', views.get_reports_for_university,
          name='get_reports_for_university'),

    Route('/search_universities/{search}', 'GET', views.search_universities,
          name='search_universities'),

    Route('/create_or_get_user/{email}', 'GET', views.create_or_get_user,
          name='create_or_get_user'),

    Route('/add_uni_to_cart/{email}/{uni_id}', 'GET', views.add_uni_to_cart,
          name='add_uni_to_cart'),

    Route('/remove_uni_from_cart/{email}/{uni_id}', 'GET', views.remove_uni_from_cart,
          name='remove_uni_from_cart'),

    Route('/remove_link_or_note/{email}', 'GET', views.remove_link_or_note,
          name='remove_link_or_note'),

    Route('/add_link_or_note/{email}', 'GET', views.add_link_or_note, name='add_link_or_note'),

    Route('/get_university_and_score', 'GET', views.get_university_and_score,
          name='get_university_and_score'),
    
    Route('/get_choropleth_countries', 'GET', views.get_choropleth_countries,
          name='get_choropleth_countries'),

    Route('/get_money_for_uni/{uni_id}', 'GET', views.get_money_for_uni,
          name='get_money_for_uni'),
    
    Route('/get_top_stared_universities/', 'GET', views.get_top_stared_universities,
          name='get_top_stared_universities'),
    
    Include('/', docs_urls),
    Include('/static', static_urls)
]
