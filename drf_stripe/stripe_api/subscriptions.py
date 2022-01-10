from itertools import chain
from operator import attrgetter
from typing import Literal

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


def list_subscriptions(status: STATUS_ARG = None, limit: int = 10, starting_after: str = None):
    """
    Retrieve all subscriptions we provide.
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
        q &= Q(status__in={StripeSubscriptionStatus.ACTIVE.value, StripeSubscriptionStatus.PAST_DUE.value,
                           StripeSubscriptionStatus.TRIALING.value})

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
    print(current_products)
    prices = Price.objects.filter(
        Q(active=True) &
        Q(product__active=True) &
        ~Q(product__product_id__in=current_products)
    )
    return prices
