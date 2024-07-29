from rest_framework.viewsets import generics
from rest_framework.permissions import AllowAny

from user.models import User
from user.serializers import RegisterSerializer


class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = RegisterSerializer
