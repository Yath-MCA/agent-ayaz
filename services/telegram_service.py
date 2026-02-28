from typing import Awaitable, Callable

from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters


class TelegramService:
    def __init__(
        self,
        token: str | None,
        allowed_user_id: int,
        message_handler: Callable[[str], Awaitable[str]],
        projects_handler: Callable[[], str],
        status_handler: Callable[[], str],
        select_project_handler: Callable[[str], str],
        current_project_handler: Callable[[], str],
        tasks_handler: Callable[[], str],
        run_task_handler: Callable[[str], str],
        run_custom_handler: Callable[[str], str],
    ) -> None:
        self.token = token
        self.allowed_user_id = allowed_user_id
        self.message_handler = message_handler
        self.projects_handler = projects_handler
        self.status_handler = status_handler
        self.select_project_handler = select_project_handler
        self.current_project_handler = current_project_handler
        self.tasks_handler = tasks_handler
        self.run_task_handler = run_task_handler
        self.run_custom_handler = run_custom_handler

    def is_allowed(self, update) -> bool:
        return (
            self.allowed_user_id > 0
            and update.effective_user is not None
            and update.effective_user.id == self.allowed_user_id
        )

    async def deny_if_not_allowed(self, update) -> bool:
        if self.is_allowed(update):
            return False
        if update.message:
            await update.message.reply_text("⛔ Unauthorized user")
        return True

    async def cmd_start(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(
            "✅ Bot connected. Use /help to see available options."
        )

    async def cmd_help(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(
            "Available commands:\n"
            "/help - show command list\n"
            "/status - show runtime status\n"
            "/projects - list projects under PROJECT_ROOT\n"
            "/project <name> - select project, open in VS Code, show run-task files\n"
            "/current - show currently selected project\n"
            "/tasks - list available files in selected project run-task folder\n"
            "/task <file_name> - run selected run-task file\n"
            "/custom <command> - run custom command in selected project\n"
            "/id - show your Telegram user ID"
        )

    async def cmd_status(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(self.status_handler()[:4000])

    async def cmd_projects(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(self.projects_handler()[:4000])

    async def cmd_project(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return

        if not context.args:
            await update.message.reply_text("Usage: /project <project_name>")
            return

        project_name = " ".join(context.args).strip()
        response = self.select_project_handler(project_name)
        await update.message.reply_text(response[:4000])

    async def cmd_tasks(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(self.tasks_handler()[:4000])

    async def cmd_current(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(self.current_project_handler()[:4000])

    async def cmd_task(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return

        if not context.args:
            await update.message.reply_text("Usage: /task <task_file_name>")
            return

        task_name = " ".join(context.args).strip()
        response = self.run_task_handler(task_name)
        await update.message.reply_text(response[:4000])

    async def cmd_custom(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return

        if not context.args:
            await update.message.reply_text("Usage: /custom <command>")
            return

        command = " ".join(context.args).strip()
        response = self.run_custom_handler(command)
        await update.message.reply_text(response[:4000])

    async def cmd_id(self, update, context) -> None:
        user = update.effective_user
        if update.message and user:
            await update.message.reply_text(f"Your Telegram user ID: {user.id}")

    async def handle_text(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )

        text = update.message.text
        reply = await self.message_handler(text)
        await update.message.reply_text(reply[:4000])

    def build_application(self):
        if not self.token:
            return None

        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("status", self.cmd_status))
        app.add_handler(CommandHandler("projects", self.cmd_projects))
        app.add_handler(CommandHandler("project", self.cmd_project))
        app.add_handler(CommandHandler("current", self.cmd_current))
        app.add_handler(CommandHandler("tasks", self.cmd_tasks))
        app.add_handler(CommandHandler("task", self.cmd_task))
        app.add_handler(CommandHandler("custom", self.cmd_custom))
        app.add_handler(CommandHandler("id", self.cmd_id))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        return app
