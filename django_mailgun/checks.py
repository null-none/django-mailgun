from functools import partial

from django.conf import global_settings, settings
from django.core import checks, mail
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .backends import EmailBackend


class MailgunSettingsCheck:
    def __call__(self, app_configs, **kwargs):
        backends = self.get_backends()
        if not backends:
            return []

        messages = []
        for create_backend in backends:
            try:
                create_backend()
            except ImproperlyConfigured as exc:
                messages.append(checks.Error(str(exc), id="django_mailgun.E001"))

        if settings.DEFAULT_FROM_EMAIL == global_settings.DEFAULT_FROM_EMAIL:
            messages.append(
                checks.Warning(
                    "DEFAULT_FROM_EMAIL is not set, so email is sent from "
                    f"{global_settings.DEFAULT_FROM_EMAIL!r}.",
                    hint="Set DEFAULT_FROM_EMAIL to an address on your Mailgun domain.",
                    id="django_mailgun.W001",
                )
            )
        if (settings.ADMINS or settings.MANAGERS) and (
            settings.SERVER_EMAIL == global_settings.SERVER_EMAIL
        ):
            messages.append(
                checks.Warning(
                    "SERVER_EMAIL is not set, so error reports are sent from "
                    f"{global_settings.SERVER_EMAIL!r}.",
                    hint="Set SERVER_EMAIL to an address on your Mailgun domain.",
                    id="django_mailgun.W002",
                )
            )
        return messages

    def get_backends(self):
        if hasattr(mail, "mailers") and hasattr(settings, "MAILERS"):
            return [
                partial(mail.mailers.__getitem__, alias)
                for alias, config in settings.MAILERS.items()
                if self.is_mailgun_backend(config.get("BACKEND"))
            ]
        if settings.is_overridden("EMAIL_BACKEND") and self.is_mailgun_backend(
            settings.EMAIL_BACKEND
        ):
            return [import_string(settings.EMAIL_BACKEND)]
        return []

    def is_mailgun_backend(self, path):
        if not isinstance(path, str):
            return False
        try:
            backend_class = import_string(path)
        except ImportError:
            return False
        return isinstance(backend_class, type) and issubclass(
            backend_class, EmailBackend
        )
