from itertools import chain
from typing import Literal

from django.db.models import Q
from django.db.models import QuerySet

from drf_stripe.stripe_api.api import stripe_api as stripe
from ..models import Subscription
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


def list_user_subscriptions(user_instance, current=True) -> QuerySet[Subscription]:
    """
    Retrieve a set of Subscriptions associated with a given User instance.

    :param user_instance: Django User instance.
    :param bool current: Defaults to True and retrieves only current subscriptions
        (excluding any cancelled, ended, unpaid subscriptions)
    """
    q = Q(user=user_instance)
    if current is True:
        q &= Q(status__in={StripeSubscriptionStatus.ACTIVE, StripeSubscriptionStatus.PAST_DUE,
                           StripeSubscriptionStatus.TRIALING})

    return Subscription.objects.filter(q)


def list_user_subscription_products(user_instance, current=True):
    """
    Retrieve a set of Product instances associated with a given User instance.

    :param user_instance: Django User instance.
    :param bool current: Defaults to True and retrieves only products associated with current subscriptions
        (excluding any cancelled, ended, unpaid subscription products)
    """
    subscription = list_user_subscriptions(user_instance, current=current)
    products = set(chain(sub.price.product for sub in subscription.prefetch_related("price__product")))
    return products
