from django.apps import AppConfig
from django.core import checks

from .checks import MailgunSettingsCheck


class DjangoMailgunConfig(AppConfig):
    name = "django_mailgun"
    verbose_name = "Mailgun"
    settings_check = MailgunSettingsCheck()

    def ready(self):
        checks.register(self.settings_check, "mail")
