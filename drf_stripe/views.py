from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_stripe.stripe_webhooks.handler import handle_stripe_webhook_request
from .serializers import SubscriptionSerializer, PriceSerializer, SubscriptionItemSerializer
from .stripe_api.checkout import stripe_api_create_checkout_session
from .stripe_api.customer_portal import stripe_api_create_billing_portal_session
from .stripe_api.customers import get_or_create_stripe_user
from .stripe_api.subscriptions import list_user_subscriptions, list_user_subscription_items, \
    list_subscribable_product_prices_to_user, list_all_available_product_prices


class Subscription(ListAPIView):
    """Subscription of current user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionSerializer
    pagination_class = None

    def get_queryset(self):
        return list_user_subscriptions(self.request.user.id)


class SubscriptionItems(ListAPIView):
    """SubscriptionItems of current user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionItemSerializer
    pagination_class = None

    def get_queryset(self):
        return list_user_subscription_items(self.request.user.id)


class SubscribableProductPrice(ListAPIView):
    """
    Products that can be subscribed.
    Depending on whether this request is made with a bearer token,
    Anonymous user will receive a list of product and prices available to the public.
    Authenticated user will receive a list of products and prices available to the user, excluding any product prices
    the user has already been subscribed to.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PriceSerializer
    pagination_class = None

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return list_all_available_product_prices()
        else:
            return list_subscribable_product_prices_to_user(self.request.user.id)


class CreateStripeCheckoutSession(APIView):
    """
    Provides session for using Stripe hosted Checkout page.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stripe_user = get_or_create_stripe_user(user_id=request.user.id)
        price_id = request.data['price_id']

        checkout_session = stripe_api_create_checkout_session(customer_id=stripe_user.customer_id, price_id=price_id)
        return Response({'session_id': checkout_session['id']}, status=status.HTTP_200_OK)


class StripeWebhook(APIView):
    """Provides endpoint for Stripe webhooks"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        handle_stripe_webhook_request(request)
        return Response(status=status.HTTP_200_OK)


class StripeCustomerPortal(APIView):
    """Provides redirect URL for Stripe customer portal."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        session = stripe_api_create_billing_portal_session(request.user.id)
        return Response({"url": session.url}, status=status.HTTP_200_OK)
