from qdrant_client.http import exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from assistant.assistant_utils import generate_response_langchain


class AIAssistant(APIView):

    def post(self, request, *args, **kwargs):
        user_question = request.data.get('message', '')
        chat_history = request.data.get('chat_history', [])
        
        if not user_question:
            return Response({'message': 'No Question asked!', 'error': True}, status=status.HTTP_400_BAD_REQUEST)

        category = request.data.get('category', '')
        country = request.data.get('country', 'PK')
        try:
            answer = generate_response_langchain(
                user_question, category, country, chat_history)
        except exceptions.UnexpectedResponse:
            return Response({'message': "Country: {} is not supported yet".format(country), 'error': True})

        return Response({'message': answer, 'error': False})
