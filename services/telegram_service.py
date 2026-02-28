from typing import Awaitable, Callable

from telegram.ext import Application, MessageHandler, filters


class TelegramService:
    def __init__(
        self,
        token: str | None,
        allowed_user_id: int,
        message_handler: Callable[[str], Awaitable[str]],
    ) -> None:
        self.token = token
        self.allowed_user_id = allowed_user_id
        self.message_handler = message_handler

    def is_allowed(self, update) -> bool:
        return self.allowed_user_id > 0 and update.effective_user.id == self.allowed_user_id

    async def handle_text(self, update, context) -> None:
        if not self.is_allowed(update):
            return

        text = update.message.text
        reply = await self.message_handler(text)
        await update.message.reply_text(reply[:4000])

    def build_application(self):
        if not self.token:
            return None

        app = Application.builder().token(self.token).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        return app
