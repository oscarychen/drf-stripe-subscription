from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from stripe.error import StripeError

from drf_stripe.models import SubscriptionItem, Product, Price, Subscription, StripeUser
from drf_stripe.stripe_api.checkout import stripe_api_create_checkout_session
from drf_stripe.stripe_api.customers import get_or_create_stripe_user
from drf_stripe.settings import drf_stripe_settings

from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = (
            "subscription_id", "period_start", "period_end", "status", "cancel_at", "cancel_at_period_end",
            "trial_start", "trial_end"
        )


class SubscriptionItemSerializer(serializers.ModelSerializer):
    """Serializes SubscriptionItem model with attributes pulled from related Subscription instance"""
    product_id = serializers.CharField(source="price.product.product_id")
    product_name = serializers.CharField(source="price.product.name")
    product_description = serializers.CharField(source="price.product.description")
    price_id = serializers.CharField(source="price.price_id")
    price_nickname = serializers.CharField(source="price.nickname")
    price = serializers.CharField(source="price.price")
    freq = serializers.CharField(source="price.freq")
    services = serializers.SerializerMethodField(method_name='get_feature_ids')
    subscription_status = serializers.CharField(source='subscription.status')
    period_start = serializers.DateTimeField(source='subscription.period_start')
    period_end = serializers.DateTimeField(source='subscription.period_end')
    trial_start = serializers.DateTimeField(source='subscription.trial_start')
    trial_end = serializers.DateTimeField(source='subscription.trial_end')
    ended_at = serializers.DateTimeField(source='subscription.ended_at')
    cancel_at = serializers.DateTimeField(source='subscription.cancel_at')
    cancel_at_period_end = serializers.BooleanField(source='subscription.cancel_at_period_end')

    def get_feature_ids(self, obj):
        return [{"feature_id": link.feature.feature_id, "feature_desc": link.feature.description} for link in
                obj.price.product.linked_features.all().prefetch_related('feature')]

    def get_subscription_expires_at(self, obj):
        return obj.subscription.period_end or \
               obj.subscription.cancel_at or \
               obj.subscription.trial_end or \
               obj.subscription.ended_at

    class Meta:
        model = SubscriptionItem
        fields = (
            "product_id", "product_name", "product_description", "price_id", "price_nickname", "price", "freq",
            "subscription_status", "period_start", "period_end",
            "trial_start", "trial_end", "ended_at", "cancel_at", "cancel_at_period_end", "services")


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
        return [{"feature_id": prod_feature.feature.feature_id, "feature_desc": prod_feature.feature.description} for
                prod_feature in
                obj.product.linked_features.all().prefetch_related("feature")]

    class Meta:
        model = Price
        fields = ("price_id", "product_id", "name", "price", "freq", "avail", "services", "currency")


class CheckoutRequestSerializer(serializers.Serializer):
    """Handles request data to create a Stripe checkout session."""
    price_id = serializers.CharField()
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    owner_type = serializers.CharField(required=False, allow_null=True)  # e.g. 'app_label.ModelName' or 'modelname'
    owner_id = serializers.CharField(required=False, allow_null=True)

    def validate(self, attrs):
        request = self.context['request']
        price_id = attrs['price_id']

        # set stripe api key
        stripe_module = __import__('stripe')
        stripe_module.api_key = drf_stripe_settings.STRIPE_API_SECRET

        # If billing model is not configured, keep legacy per-user flow (StripeUser)
        billing_model_path = drf_stripe_settings.BILLING_ACCOUNT_MODEL
        BillingModel = None
        if billing_model_path:
            try:
                app_label, model_name = billing_model_path.split('.', 1)
                BillingModel = django_apps.get_model(app_label, model_name)
            except Exception:
                # allow full label as fallback
                try:
                    BillingModel = django_apps.get_model(billing_model_path)
                except Exception:
                    BillingModel = None

        # Determine customer: either BillingModel (if configured) or legacy StripeUser
        customer_id = None
        billing_account_instance = None

        if BillingModel:
            # Use provided owner_type/owner_id if given, else default to current user owner
            owner_type = attrs.get('owner_type')
            owner_id = attrs.get('owner_id')
            try:
                if owner_type and owner_id:
                    # owner_type may be 'app_label.ModelName' or 'modelname'
                    if '.' in owner_type:
                        owner_app_label, owner_model = owner_type.split('.', 1)
                        owner_cls = django_apps.get_model(owner_app_label, owner_model)
                    else:
                        owner_cls = None
                        for app_config in django_apps.get_app_configs():
                            try:
                                owner_cls = django_apps.get_model(app_config.label, owner_type)
                                break
                            except Exception:
                                continue
                    if owner_cls is None:
                        raise ValidationError(f"Unknown owner_type {owner_type}")
                    owner_obj = owner_cls.objects.get(pk=owner_id)
                else:
                    # default: assume billing model keyed by request.user
                    owner_obj = request.user

                # Attempt to find or create a BillingModel instance.
                billing_account_instance = None
                # Pattern 1: BillingModel uses Generic relation content_type/object_id
                if hasattr(BillingModel, 'content_type'):
                    ct = ContentType.objects.get_for_model(owner_obj.__class__)
                    billing_account_instance, _ = BillingModel.objects.get_or_create(content_type=ct, object_id=owner_obj.pk)
                else:
                    # Pattern 2: BillingModel has an FK field to the owner with common names
                    for field_name in ('owner', 'user', 'organization', 'team'):
                        if field_name in [f.name for f in BillingModel._meta.get_fields()]:
                            kwargs = {field_name: owner_obj}
                            billing_account_instance, _ = BillingModel.objects.get_or_create(**kwargs)
                            break
                    if billing_account_instance is None:
                        # Last resort try get_or_create by pk if possible
                        try:
                            billing_account_instance, _ = BillingModel.objects.get_or_create(pk=getattr(owner_obj, 'pk', None))
                        except Exception:
                            raise ValidationError("Cannot create or resolve billing account for given owner")

                # Authorization: ensure request.user can perform payment if they attempt to create/manage checkout for an owner
                if hasattr(billing_account_instance, 'can_manage_billing'):
                    if not billing_account_instance.can_manage_billing(request.user):
                        raise ValidationError("User is not authorized to manage billing for this account.")

                # Create/get stripe customer
                try:
                    customer_id = billing_account_instance.get_or_create_stripe_customer(
                        stripe_module,
                        email=getattr(request.user, drf_stripe_settings.DJANGO_USER_EMAIL_FIELD, None),
                        metadata={"owner_type": getattr(owner_obj.__class__, '__name__', ''), "owner_id": str(getattr(owner_obj, 'pk', ''))}
                    )
                except TypeError:
                    customer_id = billing_account_instance.get_or_create_stripe_customer(stripe_module)
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(f"Failed to resolve billing account: {e}")

        else:
            # Legacy per-user flow using package helper
            try:
                stripe_user = get_or_create_stripe_user(user_id=request.user.id)
                customer_id = stripe_user.customer_id
            except Exception as e:
                raise ValidationError(f"Failed to resolve legacy Stripe user: {e}")

        # Create checkout session using customer_id (prefer package helper)
        try:
            try:
                checkout_session = stripe_api_create_checkout_session(customer_id=customer_id, price_id=price_id)
            except TypeError:
                # fallback direct call
                checkout_session = stripe_module.checkout.Session.create(
                    payment_method_types=drf_stripe_settings.DEFAULT_PAYMENT_METHOD_TYPES,
                    mode=drf_stripe_settings.DEFAULT_CHECKOUT_MODE,
                    line_items=[{"price": price_id, "quantity": getattr(billing_account_instance, "seats", drf_stripe_settings.DEFAULT_MAX_SUBSCRIPTION_QUANTITY)}],
                    customer=customer_id,
                    success_url=f"{drf_stripe_settings.FRONT_END_BASE_URL}/{drf_stripe_settings.CHECKOUT_SUCCESS_URL_PATH}",
                    cancel_url=f"{drf_stripe_settings.FRONT_END_BASE_URL}/{drf_stripe_settings.CHECKOUT_CANCEL_URL_PATH}",
                    metadata={"owner_type": getattr(billing_account_instance.__class__, '__name__', '') if billing_account_instance else 'user', "owner_id": str(getattr(billing_account_instance, 'pk', getattr(request.user, 'pk', '')))}
                )
            attrs['session_id'] = checkout_session['id']
        except StripeError as e:
            raise ValidationError(e.error)
        except Exception as e:
            raise ValidationError(str(e))

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
