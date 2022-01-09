from rest_framework import serializers

from drf_stripe.models import SubscriptionItem


class StripePlanSerializer(serializers.Serializer):
    id = serializers.CharField()
    amount = serializers.IntegerField()
    currency = serializers.CharField()
    interval = serializers.CharField()
    interval_count = serializers.IntegerField()


class SubscriptionSerializer(serializers.Serializer):
    subscription_id = serializers.CharField()
    billing_cycle_anchor = serializers.IntegerField(required=False)
    created = serializers.IntegerField(required=False)
    current_period_start = serializers.IntegerField(required=False)
    current_period_end = serializers.IntegerField(required=False)
    latest_invoice = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    plan = StripePlanSerializer(required=False)


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
