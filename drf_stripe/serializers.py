from rest_framework import serializers

from drf_stripe.models import SubscriptionItem, Product, Price, Subscription


class StripeSubscriptionItemSerializer(serializers.ModelSerializer):
    """Serializes SubscriptionItem model with attributes pulled from related Subscription instance"""
    product_id = serializers.CharField(source="price.product.product_id")
    price_id = serializers.CharField(source="price.price_id")
    price = serializers.CharField(source="price.price")
    freq = serializers.CharField(source="price.freq")
    services = serializers.SerializerMethodField(method_name='get_feature_ids')
    subscription_expires_at = serializers.SerializerMethodField(method_name='get_subscription_expires_at')
    subscription_status = serializers.CharField(source='subscription.status')

    def get_feature_ids(self, obj):
        return {link.feature.feature_id for link in obj.price.product.linked_features.all().prefetch_related('feature')}

    def get_subscription_expires_at(self, obj):
        return obj.subscription.period_end or \
               obj.subscription.cancel_at or \
               obj.subscription.trial_end or \
               obj.subscription.ended_at

    class Meta:
        model = SubscriptionItem
        fields = (
            "product_id", "price_id", "price", "freq", "services", "subscription_expires_at", "subscription_status")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class PriceSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(source="product.product_id")
    name = serializers.CharField(source="product.name")
    avail = serializers.BooleanField(source="active")
    services = serializers.SerializerMethodField(method_name='get_feature_ids')

    def get_feature_ids(self, obj):
        return {feature.feature_id for feature in obj.product.linked_features.all().prefetch_related("feature")}

    class Meta:
        model = Price
        fields = ("price_id", "product_id", "name", "price", "freq", "avail", "services")


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = (
            "subscription_id", "period_start", "period_end", "status", "cancel_at", "cancel_at_period_end",
            "trial_start", "trial_end"
        )
