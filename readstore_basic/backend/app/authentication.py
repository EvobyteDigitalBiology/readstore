import base64

from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed

from django.db.models import Q

from django.contrib.auth.models import User


class RSClientTokenAuth(BasicAuthentication):
    def authenticate(self, request):
        # Get the 'Authorization' header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None  # No authentication header provided
        
        if not auth_header.startswith('Basic '):
            return None
        
        # Decode the base64 encoded string
        encoded_credentials = auth_header.split(' ')[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, token = decoded_credentials.split(':', 1)
        
        # Check if username is part of appuser group
        usercheck1 = Q(username=username) & Q(groups__name='appuser')
        
        # Check if request user is found and if otken is valid
        if User.objects.filter(usercheck1).exists():
            user = User.objects.get(usercheck1)

            if user.appuser.token == token:
                return (user, None)
            else:
                raise AuthenticationFailed('Invalid token')
        else:
            raise AuthenticationFailed('Invalid user')