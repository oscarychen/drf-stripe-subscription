# drf-stripe-subscription

An out-of-box Django REST framework solution for payment and subscription management using Stripe. The goal of this
package is to utilize Stripe provided UI and features as much as possible to manage subscription product models. This
package helps you make use of Stripe's hosted UI for customer checkout, billing management, as well as for admin to
manage product, pricing, and customer subscriptions.

- Django data models representing Stripe data objects
- Stripe Webhooks for managing changes with your products, prices, and customer subscriptions
- Django management commands for synchronizing data with Stripe
- Django REST API endpoints supporting Stripe Checkout Session, Customer Portal, as well as fetching products, prices,
  and subscriptions

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

Pull Product and Price data from Stripe into Django database using the following command:

```commandline
python manage.py update_stripe_products
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

### Created a checkout session using Stripe hosted Checkout page

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
either `mysite.com/payment/session={{CHECKOUT_SESSION_ID}}` if the checkout is successful,
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

- Manage your product and pricing model from Stripe Portal, and rely on webhook to update your Django application
  automatically.
- Manage your customer subscriptions from Stripe Portal, and rely on webhook to update your Django application
  automatically.