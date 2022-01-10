from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SubscriptionSerializer, PriceSerializer
from .stripe_api.checkout import stripe_api_create_checkout_session
from .stripe_api.customers import get_or_create_stripe_user
from .stripe_api.subscriptions import list_user_subscriptions, \
    list_subscribable_product_prices_to_user
from .stripe_api.webhooks import handle_stripe_webhook_request


class Subscription(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get list of subscriptions that user currently has."""

        # # TODO: temporary accommodation to requests with JWT Token User
        # user = get_user_model().objects.get(id=request.user.id)
        # # user = request.user
        # subscriptions = user.stripe_user.current_subscriptions
        subscriptions = list_user_subscriptions(request.user.id)
        return Response(SubscriptionSerializer(subscriptions, many=True).data, status=status.HTTP_200_OK)


class CreateStripeCheckoutSession(APIView):
    """
    Provides session for using Stripe hosted Checkout page.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = get_user_model().objects.get(id=request.user.id)
        # current_subscriptions = list_user_subscription_products(user)
        # if current_subscriptions:
        #     return Response({'message': 'You currently already have active subscription.'},
        #                     status=status.HTTP_409_CONFLICT)

        get_or_create_stripe_user(user)
        price_id = request.data['price_id']

        checkout_session = stripe_api_create_checkout_session(user, price_id)
        return Response({'sessionId': checkout_session['id']}, status=status.HTTP_200_OK)


class StripeWebhook(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        handle_stripe_webhook_request(request)
        return Response(status=status.HTTP_200_OK)


class SubscribableProductPrice(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prices = list_subscribable_product_prices_to_user(request.user.id)
        return Response(PriceSerializer(prices, many=True).data, status=status.HTTP_200_OK)
