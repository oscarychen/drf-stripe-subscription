from django.urls import path

from drf_stripe import views

urlpatterns = [
    path('checkout/', views.CreateStripeCheckoutSession.as_view()),
    path('webhook/', views.StripeWebhook.as_view()),
]
