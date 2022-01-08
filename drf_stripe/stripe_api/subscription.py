from typing import Literal

import stripe

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
    Retrieve subscriptions from Stripe
    """
    stripe.Subscription.list(status=status, limit=limit, starting_after=starting_after)
