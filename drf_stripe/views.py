from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .stripe_api.checkout import stripe_api_create_checkout_session
from .stripe_api.customers import get_or_create_stripe_user
from .stripe_api.subscriptions import list_user_subscription_products
from .stripe_api.webhooks import handle_stripe_webhook_request


class Subscription(APIView):

    def get(self, request):
        """Get list of subscriptions that user currently has."""

        # TODO: temp accommodation due to custom auth backend not ready in main project
        user = get_user_model().objects.get(id=request.user.id)  # request.user


class CreateStripeCheckoutSession(APIView):
    """
    Provides session for using Stripe hosted Checkout page.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = get_user_model().objects.get(id=request.user.id)
        current_subscriptions = list_user_subscription_products(user)
        if current_subscriptions:
            return Response({'message': 'You currently already have active subscription.'},
                            status=status.HTTP_409_CONFLICT)

        get_or_create_stripe_user(user)
        price_id = request.data['price_id']

        checkout_session = stripe_api_create_checkout_session(user, price_id)
        return Response({'sessionId': checkout_session['id']}, status=status.HTTP_200_OK)


class StripeWebhook(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        handle_stripe_webhook_request(request)
        return Response(status=status.HTTP_200_OK)
