# django-mailgun

Send Django email with the [Mailgun](https://www.mailgun.com/) HTTP API.

## Install

```bash
pip install git+https://github.com/null-none/django-mailgun.git
```

## Settings

```python
INSTALLED_APPS = [..., "django_mailgun"]

DEFAULT_FROM_EMAIL = "noreply@mg.example.com"
```

Django 6.1 and newer:

```python
MAILERS = {
    "default": {
        "BACKEND": "django_mailgun.backends.EmailBackend",
        "OPTIONS": {
            "api_key": os.environ["MAILGUN_API_KEY"],
            "domain": "mg.example.com",
        },
    },
}
```

Django 5.2 and 6.0:

```python
EMAIL_BACKEND = "django_mailgun.backends.EmailBackend"
MAILGUN_API_KEY = os.environ["MAILGUN_API_KEY"]
MAILGUN_DOMAIN = "mg.example.com"
```

| Option | Setting | Default |
|---|---|---|
| `api_key` | `MAILGUN_API_KEY` | required |
| `domain` | `MAILGUN_DOMAIN` | required |
| `api_url` | `MAILGUN_API_URL` | `https://api.mailgun.net/v3` (EU: `https://api.eu.mailgun.net/v3`) |
| `timeout` | `MAILGUN_TIMEOUT` | `10` seconds |

## Check

```bash
python manage.py check
python manage.py sendtestemail you@example.com
```

## Usage

```python
from django.core.mail import send_mail

send_mail("Hello", "Hi there!", None, ["user@example.com"])
```

HTML, attachments, cc and bcc work as usual. You can set [Mailgun options](https://documentation.mailgun.com/docs/mailgun/user-manual/sending-messages/send-smtp) with headers, for example `headers={"X-Mailgun-Tag": "welcome"}`.

Mailgun errors raise `django_mailgun.exceptions.MailgunAPIError`.
