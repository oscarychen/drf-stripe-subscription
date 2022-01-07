from functools import cached_property

from django.contrib.auth import get_user_model
from django.db import models


class StripeUser(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='stripe_user', primary_key=True)
    stripe_id = models.CharField(max_length=128)

    @cached_property
    def current_subscriptions(self):
        """Return query set of Subscription instances that the user currently has."""
        return self.subscriptions

    def get_subscribed_services(self):
        """List of services that the user currently has access to."""
        # TODO: implementation

    def get_subscribed_products(self):
        """List of product ides that the user currently has access to."""
        # TODO: implementation


class Feature(models.Model):
    """A model used to keep track of features provided by your application."""
    feature_id = models.CharField(max_length=64, primary_key=True)
    description = models.CharField(max_length=256)


class Price(models.Model):
    """A model representing to a Stripe Price object, with enhanced attributes."""
    price_id = models.CharField(max_length=256, primary_key=True)
    product_id = models.CharField(max_length=256)
    name = models.CharField(max_length=256)  # displayed name
    price = models.PositiveIntegerField()  # price in cents, corresponding to Stripe unit_amount
    # billing frequency, translated from Stripe price.recurring.interval and price.recurring.interval_count
    freq = models.CharField()
    avail = models.BooleanField()  # available of the price, used to supress a price

    class Meta:
        indexes = [
            models.Index(fields=['avail'])
        ]


class PriceFeature(models.Model):
    """A model representing association of Price and Feature instances. They have many-to-many relationship."""
    price = models.ForeignKey(Price, on_delete=models.CASCADE, related_name="related_features")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="related_prices")


class Subscription(models.Model):
    """
    A model representing the association of User and Price, corresponding to a Stripe Subscription object single
    line item.
    """
    subscription_id = models.CharField(max_length=256, primary_key=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="subscriptions")
    price = models.ForeignKey(Price, on_delete=models.CASCADE, related_name="+")
    period_start = models.DateTimeField(null=True)
    period_end = models.DateTimeField(null=True)
    cancel_at = models.DateTimeField(null=True)
    cancel_at_period_end = models.BooleanField()
    ended_at = models.DateTimeField(null=True)
    status = models.CharField()
    trial_end = models.DateTimeField(null=True)
    trial_start = models.DateTimeField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status'])
        ]
