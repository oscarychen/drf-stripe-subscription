from itertools import chain
from operator import attrgetter
from typing import Literal, List

from django.db.models import Q
from django.db.models import QuerySet

from drf_stripe.stripe_api.api import stripe_api as stripe
from ..models import Subscription, Price
from ..stripe_models.subscription import StripeSubscriptionStatus

"""
status argument, see https://stripe.com/docs/api/subscriptions/list?lang=python#list_subscriptions-status
"""
STATUS_ARG = Literal[
    "active",
    "past_due",
    "unpaid",
    "canceled",
    "incomplete",
    "incomplete_expired",
    "trialing",
    "all",
    "ended"
]


def stripe_api_list_subscriptions(status: STATUS_ARG = None, limit: int = 100, starting_after: str = None):
    """
    Retrieve all subscriptions.

    """
    stripe.Subscription.list(status=status, limit=limit, starting_after=starting_after)


def list_user_subscriptions(user_id, current=True) -> QuerySet[Subscription]:
    """
    Retrieve a set of Subscriptions associated with a given User instance.

    :param user_id: Django User id.
    :param bool current: Defaults to True and retrieves only current subscriptions
        (excluding any cancelled, ended, unpaid subscriptions)
    """
    q = Q(user_id=user_id)
    if current is True:
        q &= Q(status__in={StripeSubscriptionStatus.ACTIVE, StripeSubscriptionStatus.PAST_DUE,
                           StripeSubscriptionStatus.TRIALING})

    return Subscription.objects.filter(q)


def list_user_subscription_products(user_id, current=True):
    """
    Retrieve a set of Product instances associated with a given User instance.

    :param user_id: Django User id.
    :param bool current: Defaults to True and retrieves only products associated with current subscriptions
        (excluding any cancelled, ended, unpaid subscription products)
    """
    subscriptions = list_user_subscriptions(user_id, current=current)
    sub_items = chain.from_iterable(
        sub.items.all() for sub in subscriptions.all().prefetch_related("items__price__product"))
    products = set(item.price.product for item in sub_items)
    return products


def list_subscribable_product_prices_to_user(user_id):
    """
    Retrieve a set of Price instances associated with Products that the User isn't currently subscribed to.

    :param user_id: Django user id.
    """
    current_products = set(map(attrgetter('product_id'), list_user_subscription_products(user_id)))
    prices = Price.objects.filter(
        Q(active=True) &
        Q(product__active=True) &
        ~Q(product__product_id__in=current_products)
    )
    return prices


def list_all_available_product_prices(expand: List = None):
    """Retrieve a set of all Price instances that are available to public."""

    prices = Price.objects.filter(Q(active=True) & Q(product__active=True))

    if expand and "feature" in expand:
        prices = prices.prefetch_related("product__linked_features__feature")

    return prices
