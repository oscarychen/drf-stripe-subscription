from django.contrib.auth import get_user_model
from rest_framework.views import APIView


class Subscription(APIView):

    def get(self, request):
        """Get list of subscriptions that user currently has."""

        # TODO: temp accommodation due to custom auth backend not ready
        user = get_user_model().objects.get(id=request.user.id)
