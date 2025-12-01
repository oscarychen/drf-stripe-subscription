from django.contrib.auth import get_user_model
from django.db import models
from django.apps import apps as django_apps
from django.conf import settings

from .stripe_models.subscription import ACCESS_GRANTING_STATUSES
from .settings import drf_stripe_settings

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


def get_drf_stripe_user_model_name():
    if drf_stripe_settings.DJANGO_USER_MODEL:
        return drf_stripe_settings.DJANGO_USER_MODEL
    else:
        return settings.AUTH_USER_MODEL


def get_drf_stripe_user_model():
    if drf_stripe_settings.DJANGO_USER_MODEL:
        return django_apps.get_model(drf_stripe_settings.DJANGO_USER_MODEL, require_ready=False)
    else:
        return get_user_model()


class StripeUser(models.Model):
    """Link between a Django user and a Stripe Customer (legacy per-user flow)."""
    user = models.OneToOneField(
        get_drf_stripe_user_model_name(),
        on_delete=models.CASCADE,
        related_name='stripe_user',
        primary_key=True
    )
    customer_id = models.CharField(max_length=128, null=True)

    @property
    def subscription_items(self):
        """Subscription items associated with this StripeUser."""
        return SubscriptionItem.objects.filter(subscription__stripe_user=self)

    @property
    def current_subscription_items(self):
        """Subscription items that currently grant access."""
        return self.subscription_items.filter(subscription__status__in=ACCESS_GRANTING_STATUSES)

    @property
    def subscribed_products(self):
        """Products the StripeUser currently has access to."""
        return {item.price.product for item in self.current_subscription_items.prefetch_related("price", "price__product")}

    @property
    def subscribed_features(self):
        """Features the StripeUser currently has access to."""
        price_list = self.current_subscription_items.values_list('price', flat=True)
        product_list = Price.objects.filter(pk__in=price_list).values_list("product", flat=True)
        return {item.feature for item in ProductFeature.objects.filter(product_id__in=product_list).prefetch_related("feature")}

    class Meta:
        indexes = [
            models.Index(fields=['user', 'customer_id'])
        ]


class Feature(models.Model):
    """Application-level feature representation tied to Stripe product metadata."""
    feature_id = models.CharField(max_length=64, primary_key=True)
    description = models.CharField(max_length=256, null=True, blank=True)


class Product(models.Model):
    """Stripe Product representation cached locally."""
    product_id = models.CharField(max_length=256, primary_key=True)
    active = models.BooleanField()
    description = models.CharField(max_length=1024, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)


class ProductFeature(models.Model):
    """Association between Product and Feature."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="linked_features")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="linked_products")


class Price(models.Model):
    """Stripe Price representation with extras for app logic."""
    price_id = models.CharField(max_length=256, primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices")
    nickname = models.CharField(max_length=256, null=True, blank=True)
    price = models.PositiveIntegerField()
    freq = models.CharField(max_length=64, null=True, blank=True)
    active = models.BooleanField()
    currency = models.CharField(max_length=3)

    class Meta:
        indexes = [
            models.Index(fields=['active', 'freq'])
        ]


class AbstractBillingAccount(models.Model):
    """Abstract billing account to extend in the project for multi-user/group billing flows."""
    stripe_customer_id = models.CharField(max_length=256, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=256, null=True, blank=True)
    manager_user = models.ForeignKey(
        get_drf_stripe_user_model_name(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    class Meta:
        abstract = True

    def has_active_subscription(self):
        """Return True when this billing account currently has a subscription id recorded."""
        return bool(self.stripe_subscription_id)

    def get_or_create_stripe_customer(self, stripe_module, **kwargs):
        """Create or return the Stripe customer id for this billing account. Projects may override."""
        if self.stripe_customer_id:
            return self.stripe_customer_id
        metadata = kwargs.pop("metadata", {}) or {}
        customer = stripe_module.Customer.create(metadata=metadata, **kwargs)
        self.stripe_customer_id = customer["id"]
        self.save(update_fields=["stripe_customer_id"])
        return self.stripe_customer_id

    def can_manage_billing(self, user):
        """Return True if the provided user is allowed to perform payment actions for this account."""
        if self.manager_user is None:
            return False
        return user.pk == getattr(self.manager_user, 'pk', None)


class Subscription(models.Model):
    """Subscription corresponding to a Stripe Subscription. Supports legacy per-user and optional billing owner."""
    subscription_id = models.CharField(max_length=256, primary_key=True)
    stripe_user = models.ForeignKey(StripeUser, on_delete=models.CASCADE, related_name="subscriptions", null=True, blank=True)
    billing_account_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name='+')
    billing_account_object_id = models.PositiveIntegerField(null=True, blank=True)

    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    cancel_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=64)
    trial_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['stripe_user', 'status']),
            models.Index(fields=['billing_account_content_type', 'billing_account_object_id', 'status'])
        ]

    @property
    def billing_account(self):
        """Return the billing account object linked to this subscription, if any."""
        if self.billing_account_content_type_id and self.billing_account_object_id:
            return self.billing_account_content_type.get_object_for_this_type(pk=self.billing_account_object_id)
        return None

    def get_owner(self):
        """Return the owning object: billing account if present, else the legacy user."""
        if self.billing_account:
            return self.billing_account
        if self.stripe_user:
            return self.stripe_user.user
        return None


class SubscriptionItem(models.Model):
    """Relation between Subscription and Price representing a subscription line item."""
    sub_item_id = models.CharField(max_length=256, primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="items")
    price = models.ForeignKey(Price, on_delete=models.CASCADE, related_name="+")
    quantity = models.PositiveIntegerField()
