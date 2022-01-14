from itertools import chain

from django.contrib.auth import get_user_model
from django.db import models

from .stripe_models.subscription import ACCESS_GRANTING_STATUSES


class StripeUser(models.Model):
    """A model linking Django user model with a Stripe User"""
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='stripe_user',
                                primary_key=True)
    customer_id = models.CharField(max_length=128, null=True)

    @property
    def subscription_items(self):
        """Returns a set of SubscriptionItem instances associated with the StripeUser"""
        return set(chain.from_iterable(
            sub.items.all().prefetch_related("subscription").prefetch_related(
                "price__product__linked_features") for sub in
            self.subscriptions.all().prefetch_related("items__price__product")))

    @property
    def current_subscription_items(self):
        """Returns a set of SubscriptionItem instances that grants current access."""
        return {item for item in self.subscription_items if item.subscription.status in ACCESS_GRANTING_STATUSES}

    @property
    def subscribed_products(self):
        """Returns a set of Product instances the StripeUser currently has"""
        return {item.price.product for item in self.current_subscription_items}

    @property
    def subscribed_features(self):
        """Returns a set of Feature instances the StripeUser has access to."""
        return set(chain.from_iterable(item.price.product.linked_features.all().prefetch_related("feature") for item in
                                       self.current_subscription_items))

    class Meta:
        indexes = [
            models.Index(fields=['user', 'customer_id'])
        ]


class Feature(models.Model):
    """
    A model used to keep track of features provided by your application.
    This does not correspond to a Stripe object, but the feature ids should be listed as
     a space delimited strings in Stripe.product.metadata.features
    """
    feature_id = models.CharField(max_length=64, primary_key=True)
    description = models.CharField(max_length=256, null=True)


class Product(models.Model):
    """A model representing a Stripe Product"""
    product_id = models.CharField(max_length=256, primary_key=True)
    active = models.BooleanField()
    description = models.CharField(max_length=1024, null=True)
    name = models.CharField(max_length=256, null=True)


class ProductFeature(models.Model):
    """A model representing association of Product and Feature instances. They have many-to-many relationship."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="linked_features")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="linked_products")


class Price(models.Model):
    """A model representing to a Stripe Price object, with enhanced attributes."""
    price_id = models.CharField(max_length=256, primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices")
    nickname = models.CharField(max_length=256, null=True)  # displayed name
    price = models.PositiveIntegerField()  # price in cents, corresponding to Stripe unit_amount
    # billing frequency, translated from Stripe price.recurring.interval and price.recurring.interval_count
    freq = models.CharField(max_length=64, null=True)
    active = models.BooleanField()

    class Meta:
        indexes = [
            models.Index(fields=['active', 'freq'])
        ]


class Subscription(models.Model):
    """
    A model representing Subscription, corresponding to a Stripe Subscription object.
    """
    subscription_id = models.CharField(max_length=256, primary_key=True)
    stripe_user = models.ForeignKey(StripeUser, on_delete=models.CASCADE, related_name="subscriptions")
    period_start = models.DateTimeField(null=True)
    period_end = models.DateTimeField(null=True)
    cancel_at = models.DateTimeField(null=True)
    cancel_at_period_end = models.BooleanField()
    ended_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=64)
    trial_end = models.DateTimeField(null=True)
    trial_start = models.DateTimeField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['stripe_user', 'status'])
        ]


class SubscriptionItem(models.Model):
    """
    A model representing relation of Price and Subscription, corresponding to Stripe Subscription line item.
    """
    sub_item_id = models.CharField(max_length=256, primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="items")
    price = models.ForeignKey(Price, on_delete=models.CASCADE, related_name="+")
    quantity = models.PositiveIntegerField()
