from django.urls import path

from assistant.views import ai_assistant


urlpatterns = [
    path('api/ai_assistant/', ai_assistant.AIAssistant.as_view(), name='assistant_api'),
]