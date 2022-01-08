from rest_framework import serializers


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
