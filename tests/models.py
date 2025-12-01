"""Test models for billing account integration tests."""
from django.db import models
from django.contrib.auth import get_user_model
from drf_stripe.models import AbstractBillingAccount


class CustomBilling(AbstractBillingAccount):
    """Test custom billing model that extends AbstractBillingAccount."""
    name = models.CharField(max_length=255)

    class Meta:
        app_label = 'tests'

    def __str__(self):
        return self.name
