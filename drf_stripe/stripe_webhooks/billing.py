import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType
from drf_stripe.settings import drf_stripe_settings

stripe.api_key = settings.STRIPE_SECRET_KEY
ENDPOINT_SECRET = settings.STRIPE_WEBHOOK_SECRET


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, ENDPOINT_SECRET)
    except Exception:
        return HttpResponse(status=400)

    typ = event['type']
    obj = event['data'].get('object') or {}

    # Only attempt billing-account mapping if user enabled BILLING_ACCOUNT_MODEL
    BillingModelPath = drf_stripe_settings.BILLING_ACCOUNT_MODEL
    BillingModel = None
    if BillingModelPath:
        try:
            app_label, model_name = BillingModelPath.split('.', 1)
            BillingModel = django_apps.get_model(app_label, model_name)
        except Exception:
            try:
                BillingModel = django_apps.get_model(BillingModelPath)
            except Exception:
                BillingModel = None

    # events that may carry subscription id
    if typ in ("checkout.session.completed", "invoice.payment_succeeded", "customer.subscription.created", "customer.subscription.updated"):
        metadata = obj.get("metadata", {}) or {}
        owner_type = metadata.get("owner_type")
        owner_id = metadata.get("owner_id")
        subscription_id = obj.get("subscription") or obj.get("id")
        customer_id = obj.get("customer")

        ba = None
        if BillingModel:
            # Try metadata mapping first
            if owner_type and owner_id:
                try:
                    target_owner = None
                    if '.' in owner_type:
                        owner_app_label, owner_model = owner_type.split('.', 1)
                        owner_cls = django_apps.get_model(owner_app_label, owner_model)
                        target_owner = owner_cls.objects.filter(pk=owner_id).first()
                    else:
                        owner_cls = None
                        for app_config in django_apps.get_app_configs():
                            try:
                                owner_cls = django_apps.get_model(app_config.label, owner_type)
                                break
                            except Exception:
                                continue
                        if owner_cls:
                            target_owner = owner_cls.objects.filter(pk=owner_id).first()

                    # If BillingModel uses Generic relation, find by content_type/object_id
                    if hasattr(BillingModel, 'content_type') and target_owner:
                        ct = ContentType.objects.get_for_model(target_owner.__class__)
                        ba = BillingModel.objects.filter(content_type=ct, object_id=target_owner.pk).first()
                    else:
                        # Try common FK names referencing owner
                        for field_name in ('owner', 'user', 'organization', 'team'):
                            try:
                                filter_kwargs = {f"{field_name}__pk": owner_id}
                                ba = BillingModel.objects.filter(**filter_kwargs).first()
                                if ba:
                                    break
                            except Exception:
                                continue
                except Exception:
                    ba = None

            # fallback: try by stripe customer id
            if not ba and customer_id:
                try:
                    ba = BillingModel.objects.filter(stripe_customer_id=customer_id).first()
                except Exception:
                    ba = None

        # If a billing-account instance is found and subscription id is present, persist it.
        if ba and subscription_id:
            try:
                ba.stripe_subscription_id = subscription_id
                ba.save(update_fields=["stripe_subscription_id"])
            except Exception:
                pass

    return HttpResponse(status=200)
