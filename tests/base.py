import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase

from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.products import stripe_api_update_products_prices


class BaseTest(TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def setup_product_prices(self):
        products = self._load_test_data("v1/api_product_list.json")
        prices = self._load_test_data("v1/api_price_list.json")
        stripe_api_update_products_prices(test_products=products, test_prices=prices)

    @staticmethod
    def setup_user_customer():
        user = get_user_model().objects.create(username="tester", email="tester1@example.com", password="12345")
        stripe_user = StripeUser.objects.create(user_id=user.id, customer_id="cus_tester")
        return user, stripe_user

    @staticmethod
    def _load_test_data(file_name):
        p = Path("tests/mock_responses") / file_name
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    @staticmethod
    def _print(v):
        print("$$$$$$$ DEBUG $$$$$")
        print(v)
        assert False
