import requests

from .exceptions import MailgunAPIError


class MailgunClient:
    DEFAULT_API_URL = "https://api.mailgun.net/v3"
    DEFAULT_TIMEOUT = 10

    def __init__(
        self, api_key, domain, *, api_url=DEFAULT_API_URL, timeout=DEFAULT_TIMEOUT
    ):
        self.domain = domain
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = ("api", api_key)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.session.close()

    def send_mime(self, message, recipients):
        return self.post(
            f"{self.domain}/messages.mime",
            data={"to": recipients},
            files={"message": ("message.mime", message)},
        )

    def post(self, path, **kwargs):
        try:
            response = self.session.post(
                f"{self.api_url}/{path}", timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            raise MailgunAPIError(f"Mailgun API request failed: {exc}") from exc
        try:
            data = response.json()
        except ValueError:
            data = {}
        if not response.ok:
            detail = data.get("message") or response.text.strip() or response.reason
            raise MailgunAPIError(
                f"Mailgun API error {response.status_code}: {detail}",
                status_code=response.status_code,
                response=response,
            )
        return data
