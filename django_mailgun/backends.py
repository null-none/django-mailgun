import email.policy
import threading
from email.headerregistry import Address, AddressHeader

import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.encoding import force_str, punycode

from .client import MailgunClient
from .exceptions import MailgunAPIError

try:
    from django.core.mail import InvalidMailer
except ImportError:
    InvalidMailer = None


class EmailBackend(BaseEmailBackend):
    def __init__(
        self,
        *,
        api_key=None,
        domain=None,
        api_url=None,
        timeout=None,
        fail_silently=False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.api_key = self.get_option(api_key, "MAILGUN_API_KEY")
        self.domain = self.get_option(domain, "MAILGUN_DOMAIN")
        self.api_url = self.get_option(
            api_url, "MAILGUN_API_URL", MailgunClient.DEFAULT_API_URL
        )
        self.timeout = self.get_option(
            timeout, "MAILGUN_TIMEOUT", MailgunClient.DEFAULT_TIMEOUT
        )
        self.fail_silently = fail_silently
        self.connection = None
        self.lock = threading.RLock()

        if not self.api_key:
            raise self.missing_option("api_key", "MAILGUN_API_KEY")
        if not self.domain:
            raise self.missing_option("domain", "MAILGUN_DOMAIN")

    def get_option(self, value, setting, default=None):
        return getattr(settings, setting, default) if value is None else value

    def missing_option(self, option, setting):
        alias = getattr(self, "alias", None)
        if alias is None:
            return ImproperlyConfigured(
                f"The {setting} setting is required to send email through Mailgun."
            )
        return InvalidMailer(
            f"OPTIONS must define {option!r} (or set settings.{setting}).",
            alias=alias,
        )

    def open(self):
        if self.connection is not None:
            return False
        self.connection = MailgunClient(
            self.api_key, self.domain, api_url=self.api_url, timeout=self.timeout
        )
        return True

    def close(self):
        if self.connection is None:
            return
        try:
            self.connection.close()
        finally:
            self.connection = None

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        with self.lock:
            new_conn_created = self.open()
            num_sent = 0
            try:
                for message in email_messages:
                    if self.send_message(message):
                        num_sent += 1
            finally:
                if new_conn_created:
                    self.close()
        return num_sent

    def send_message(self, email_message):
        if not email_message.recipients():
            return False
        recipients = [self.prep_address(addr) for addr in email_message.recipients()]
        if django.VERSION >= (6, 0):
            message = email_message.message(policy=email.policy.SMTP).as_bytes()
        else:
            message = email_message.message().as_bytes(linesep="\r\n")
        try:
            response = self.connection.send_mime(message, recipients)
        except MailgunAPIError:
            if not self.fail_silently:
                raise
            return False
        email_message.mailgun_id = response.get("id")
        return True

    def prep_address(self, address):
        address = force_str(address)
        parsed = AddressHeader.value_parser(address)
        defects = sorted({str(defect) for defect in parsed.all_defects})
        if defects:
            raise ValueError(f"Invalid address {address!r}: {'; '.join(defects)}")

        mailboxes = parsed.all_mailboxes
        if len(mailboxes) != 1:
            raise ValueError(f"Invalid address {address!r}: must be a single address")

        mailbox = mailboxes[0]
        if not mailbox.domain.isascii():
            domain = punycode(mailbox.domain)
            return str(Address(username=mailbox.local_part, domain=domain))
        return mailbox.addr_spec
