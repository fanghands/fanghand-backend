from loguru import logger

from app.config import settings


class EmailService:
    """Transactional email service (Resend integration)."""

    def __init__(self) -> None:
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.FROM_EMAIL

    async def send_welcome(self, email: str, username: str) -> None:
        """Send welcome email to a new user.

        Args:
            email: Recipient email address.
            username: The user's display name or username.
        """
        # TODO: real Resend integration via resend.Emails.send()
        logger.info(
            "Email send_welcome (stub): to={} username={}",
            email,
            username,
        )

    async def send_activation_confirmed(self, email: str, hand_name: str) -> None:
        """Send activation confirmation email.

        Args:
            email: Recipient email address.
            hand_name: Name of the activated Hand.
        """
        # TODO: real Resend integration
        logger.info(
            "Email send_activation_confirmed (stub): to={} hand={}",
            email,
            hand_name,
        )

    async def send_payment_failed(self, email: str, hand_name: str) -> None:
        """Send payment failure notification.

        Args:
            email: Recipient email address.
            hand_name: Name of the Hand whose payment failed.
        """
        # TODO: real Resend integration
        logger.info(
            "Email send_payment_failed (stub): to={} hand={}",
            email,
            hand_name,
        )

    async def send_trial_ending(
        self, email: str, hand_name: str, days_left: int
    ) -> None:
        """Send trial ending reminder.

        Args:
            email: Recipient email address.
            hand_name: Name of the Hand.
            days_left: Number of days remaining in the trial.
        """
        # TODO: real Resend integration
        logger.info(
            "Email send_trial_ending (stub): to={} hand={} days_left={}",
            email,
            hand_name,
            days_left,
        )


email_service = EmailService()
