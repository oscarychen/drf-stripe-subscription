from django.contrib import admin
from django.urls import include, path

admin.autodiscover()

urlpatterns = [
    path("stripe/", include("drf_stripe.urls"))
]
