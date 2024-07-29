from django.urls import path

from document_manager.views.categories_by_country import GetCategories

urlpatterns = [
    path(
        'api/categories/<str:country_code>/',  GetCategories.as_view(), name='categories_by_country'
    )
]