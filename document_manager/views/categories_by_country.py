from rest_framework.response import Response
from rest_framework.views import APIView

from document_manager.models import Document


class GetCategories(APIView):

    def get(self, request, country_code):
        categories = Document.objects.filter(country=country_code.upper()).values_list('category').distinct()
        flattened_categories = [category[0] for category in categories]
        return Response(flattened_categories)