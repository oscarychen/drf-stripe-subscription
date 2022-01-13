from django.urls import path

from drf_stripe import views

urlpatterns = [
    path('my-subscription/', views.Subscription.as_view()),
    path('my-subscription-items/', views.SubscriptionItems.as_view()),
    path('subscribable-product/', views.SubscribableProductPrice.as_view()),
    path('checkout/', views.CreateStripeCheckoutSession.as_view()),
    path('webhook/', views.StripeWebhook.as_view()),
    path('customer-portal/', views.StripeCustomerPortal.as_view())
]
