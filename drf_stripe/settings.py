from django.conf import settings
from django.test.signals import setting_changed

USER_SETTINGS = getattr(settings, "DRF_STRIPE", None)

DEFAULTS = {
    "STRIPE_API_SECRET": "my_stripe_api_key",
    "STRIPE_WEBHOOK_SECRET": "my_stripe_webhook_key",
    "FRONT_END_BASE_URL": "http://localhost:3000",
    "NEW_USER_FREE_TRIAL_DAYS": 15
}


class DrfStripeSettings:
    def __init__(self, user_settings=None, defaults=None):
        self._user_settings = user_settings or {}
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "DRF_STRIPE", {})
        return self._user_settings

    def __getattr__(self, attr):

        # check the setting is accepted
        if attr not in self.defaults:
            raise AttributeError(f"Invalid DRF_STRIPE setting: {attr}")

        # get from user settings or default value
        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]

        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


drf_stripe_settings = DrfStripeSettings(USER_SETTINGS, DEFAULTS)


def reload_drf_stripe_settings(*args, **kwargs):
    print("Reloading drf_stripe settings")
    setting = kwargs["setting"]
    if setting == "DRF_STRIPE":
        drf_stripe_settings.reload()


setting_changed.connect(reload_drf_stripe_settings)
