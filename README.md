# drf-stripe-subscription

[![CI tests](https://github.com/oscarychen/drf-stripe-subscription/actions/workflows/test.yml/badge.svg)](https://github.com/oscarychen/drf-stripe-subscription/actions/workflows/test.yml)
[![Package Downloads](https://img.shields.io/pypi/dm/drf-stripe-subscription)](https://pypi.org/project/drf-stripe-subscription/)

An out-of-box Django REST framework solution for payment and subscription management using Stripe. The goal of this
package is to utilize Stripe provided UI and features as much as possible to manage subscription product models. This
package helps you make use of Stripe's hosted UI for customer checkout, billing management, as well as for admin to
manage product, pricing, and customer subscriptions.

- Django data models representing Stripe data objects
- Supports Stripe Webhook for managing changes with your products, prices, and customer subscriptions
- Django management commands for synchronizing data with Stripe
- Django REST API endpoints supporting Stripe Checkout Session and Customer Portal

## Installation & Setup

```commandline
pip install drf-stripe-subscription
```

Include the following drf_stripe settings in Django project settings.py:

```python
DRF_STRIPE = {
    "STRIPE_API_SECRET": "my_stripe_api_key",
    "STRIPE_WEBHOOK_SECRET": "my_stripe_webhook_key",
    "FRONT_END_BASE_URL": "http://localhost:3000",
}
```

Include drf_stripe in Django INSTALLED_APPS setting:

```python
INSTALLED_APPS = (
    ...,
    "rest_framework",
    "drf_stripe",
    ...
)
```

Include drf_stripe.url routing in Django project's urls.py, ie:

```python
from django.urls import include, path

urlpatterns = [
    path("stripe/", include("drf_stripe.urls")),
    ...
]
```

Run migrations command:

```commandline
python manage.py migrate
```

Pull data from Stripe into Django database using the following command:

```commandline
python manage.py pull_stripe
```

Finally, start Django development server

```commandline
python manage.py runserver
```

as well as Stripe CLI to forward Stripe webhook requests:

```commandline
stripe listen --forward-to 127.0.0.1:8000/stripe/webhook/
```

## Usage

The following REST API endpoints are provided:

### List product prices to subscribe

```
my-site.com/stripe/subscribable-product/
```

This endpoint is available to both anonymous users and authenticated users. Anonymous users will see a list of all
currently available products. For authenticated users, this will be a list of currently available products without any
products that the user has already subscribed currently.

### List user's current subscriptions

```
my-site.com/stripe/my-subscription/
```

This endpoint provides a list of active subscriptions for the current user.

### List user's current subscription items

```
my-site.com/stripe/my-subscription-items/
```

This endpoint provides a list of active subscription items for the current user.

### Create a checkout session using Stripe hosted Checkout page

```
my-site.com/stripe/checkout/
```

This endpoint creates Stripe Checkout Session

Make request with the follow request data:

```{"price_id": "price_stripe_price_id_to_be_checked_out"}```

The response will contain a session_id which can be used by Stripe:

```{"session_id": "stripe_checkout_session_id"}```

This session_id is a unique identifier for a Stripe Checkout Session, and can be used
by [`redirectToCheckout` in Stripe.js](https://stripe.com/docs/js/checkout/redirect_to_checkout). You can implement this
in your frontend application to redirect to a Stripe hosted Checkout page after fetching the session id.

By default, the Stripe Checkout page will redirect the user back to your application at
either `mysite.com/payment/session={CHECKOUT_SESSION_ID}` if the checkout is successful,
or `mysite.com/manage-subscription/` if checkout is cancelled.

### Stripe Customer Portal

```
mysite.com/stripe/customer-portal
```

This will create a Stripe billing portal session, and return the url to that session:

```{"url": "url_to_Stripe_billing_portal_session"```

This is a link that you can use in your frontend application to redirect a user to Stripe Customer Portal and back to
your application. By default, Stripe Customer Portal will redirect the user back to your frontend application
at `my-site.com/manage-subscription/`

### Stripe Webhook

```
mysite.com/stripe/webhook/
```

This the REST API endpoint Stripe servers can call to update your Django backend application. The following Stripe
webhook events are currently supported:

```
product.created
product.updated
product.deleted
price.created
price.updated
price.deleted
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
```

With these Stripe events, you can:

- Manage your products and pricing model from Stripe Portal, and rely on webhook to update your Django application
  automatically.
- Manage your customer subscriptions from Stripe Portal, and rely on webhook to update your Django application
  automatically.

## StripeUser

The StripeUser model comes with a few attributs that allow accessing information about the user quickly:

```python
from drf_stripe.models import StripeUser

stripe_user = StripeUser.objects.get(user_id=django_user_id)

print(stripe_user.subscription_items)
print(stripe_user.current_subscription_items)
print(stripe_user.subscribed_products)
print(stripe_user.subscribed_features)
```

## Customizing Checkout Session Parameters

Some of the checkout parameters are specified in `DRF_STRIPE` settings:

`CHECKOUT_SUCCESS_URL_PATH`: The checkout session success redirect url path.
`CHECKOUT_CANCEL_URL_PATH`: The checkout session cancel redirect url path.
`PAYMENT_METHOD_TYPES`: The default
default [payment method types](https://stripe.com/docs/api/checkout/sessions/create#create_checkout_session-payment_method_types)
, defaults to `["card"]`.
`DEFAULT_CHECKOUT_MODE`: The default checkout mode, defaults to `"subscription"`.

By default, you can create a checkout session by calling the default REST endpoint `my-site.com/stripe/checkout/`, this
REST endpoint utilizes `drf_stripe.serializers.CheckoutRequestSerializer` to validate checkout parameters and create a
Stripe Checkout Session. Only a `price_id` is needed, `quantity` defaults to 1.

You can extend this serializer and customize Checkout behavior, such as specifying multiple `line_items`
, `payment_method_types`, and `checkout_mode`:

```python
from drf_stripe.stripe_api.customers import get_or_create_stripe_user
from drf_stripe.stripe_api.checkout import stripe_api_create_checkout_session
from drf_stripe.serializers import CheckoutRequestSerializer
from rest_framework.exceptions import ValidationError
from stripe.error import StripeError


class CustomCheckoutRequestSerializer(CheckoutRequestSerializer):
    """Handle creation of a custom checkout session where parameters are customized."""

    def validate(self, attrs):
        stripe_user = get_or_create_stripe_user(user_id=self.context['request'].user.id)
        try:
            checkout_session = stripe_api_create_checkout_session(
                customer_id=stripe_user.customer_id,
                line_items=[
                    {"price_id": "stripe_price_id", "quantity": 2}, ...
                ],
                payment_method_types=["card", "alipay", ...],
                checkout_mode="subscription")
            attrs['session_id'] = checkout_session['id']
        except StripeError as e:
            raise ValidationError(e.error)
        return attrs
```

For more information regarding `line_items`, `payment_method_types`, `checkout_mode`, checkout Stripe documentation for
[creating a checkout session](https://stripe.com/docs/api/checkout/sessions/create).

## Product features

Stripe does not come with a way of managing features specific to your products and application. drf-stripe-subscription
provides additional tables to manage features associated with each Stripe Product:

- Feature: this table contains feature_id and a description for the feature.
- ProductFeature: this table keeps track of the many-to-many relation between Product and Feature.

To assign features to a product, go to Stripe Dashboard -> `Products` -> `Add Product`/`Edit Product`:
Under `Product information`, click on `Additional options`, `add metadata`.

Add an entry called `features`, the value of the entry should be a space-delimited string describing a set of features,
ie: `FEATURE_A FEATURE_B FEATURE_C`.

If you have Stripe CLI webhook running, you should see that your Django server has automatically received product
information update, and created/updated the associated ProductFeature and Feature instances. Otherwise, you can also run
the `python manage.py update_stripe_products` command again to synchronize all of your product data. The `description`
attribute of each Feature instance will default to the same value as `feature_id`, you should update the `description`
yourself if needed.

## Django management commands

```commandline
python manage.py pull_stripe
```

This command calls `update_stripe_products`, `update_stripe_customers`, `update_stripe_subscriptions` commands.

```commandline
python manage.py update_stripe_products
```

Pulls products and prices from Stripe and updates Django database.

```commandline
python manage.py update_stripe_customers
```

Pulls customers from Stripe and updates Django database.

```commandline
python manage.py update_stripe_subscriptions
```

Pulls subscriptions from Stripe and updates Django database.

## Working with customized Django User models

The following DRF_STRIPE settings can be used to customize how Django creates User instance using Stripe Customer
attributes (default values shown):

```python
DRF_STRIPE = {
    "DJANGO_USER_EMAIL_FIELD": "email",
    "USER_CREATE_DEFAULTS_ATTRIBUTE_MAP": {"username": "email"},
}
```

The `DJANGO_USER_EMAIL_FIELD` specifies name of the Django User attribute to be used to store Stripe Customer email. It
will be used to look up existing Django User using Stripe Customer email.

The `USER_CREATE_DEFAULTS_ATTRIBUTE_MAP` maps the name of Django User attribute to name of corresponding Stripe Customer
attribute, and is used during the automated Django User instance creation.
