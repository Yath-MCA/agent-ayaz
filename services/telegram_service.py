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
        run_all_tasks_handler: Callable[[], Awaitable[str]],
        approve_handler: Callable[[str], str],
        reject_handler: Callable[[str], str],
        queue_status_handler: Callable[[], str],
        queue_run_handler: Callable[[], Awaitable[str]],
        promote_later_handler: Callable[[], str],
        git_commit_handler: Callable[[str, str, str, bool], str],
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
        self.run_all_tasks_handler = run_all_tasks_handler
        self.approve_handler = approve_handler
        self.reject_handler = reject_handler
        self.queue_status_handler = queue_status_handler
        self.queue_run_handler = queue_run_handler
        self.promote_later_handler = promote_later_handler
        self.git_commit_handler = git_commit_handler

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
            "/runtasks - run all tasks in run-task folder in order\n"
            "/qstatus - show queue/later/completed task status\n"
            "/qrun - process all tasks in queue/ in order\n"
            "/qlater - promote later/ tasks into queue/ (when queue is empty)\n"
            "/gitcommit [--jira ABC-123] [--remark \"note\"] [--path /repo] [--no-push] - auto-commit git changes\n"
            "/approve <token> - approve a pending task execution\n"
            "/reject <token> - reject a pending task execution\n"
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

    async def cmd_runtasks(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        response = await self.run_all_tasks_handler()
        await update.message.reply_text(response[:4000])

    async def cmd_approve(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /approve <token>")
            return
        token = context.args[0].strip()
        response = self.approve_handler(token)
        await update.message.reply_text(response[:4000])

    async def cmd_reject(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /reject <token>")
            return
        token = context.args[0].strip()
        response = self.reject_handler(token)
        await update.message.reply_text(response[:4000])

    async def cmd_qstatus(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(self.queue_status_handler()[:4000])

    async def cmd_qrun(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        response = await self.queue_run_handler()
        await update.message.reply_text(response[:4000])

    async def cmd_qlater(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        await update.message.reply_text(self.promote_later_handler()[:4000])

    async def cmd_gitcommit(self, update, context) -> None:
        if await self.deny_if_not_allowed(update):
            return
        
        # Parse arguments: /gitcommit [--jira ABC-123] [--remark "text"] [--no-push]
        args = context.args if context.args else []
        
        jira = None
        remark = None
        no_push = False
        path = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--jira" and i + 1 < len(args):
                jira = args[i + 1]
                i += 2
            elif arg == "--remark" and i + 1 < len(args):
                remark = args[i + 1]
                i += 2
            elif arg == "--path" and i + 1 < len(args):
                path = args[i + 1]
                i += 2
            elif arg == "--no-push":
                no_push = True
                i += 1
            else:
                i += 1
        
        result = self.git_commit_handler(path, jira, remark, no_push)
        await update.message.reply_text(result[:4000])

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
        app.add_handler(CommandHandler("runtasks", self.cmd_runtasks))
        app.add_handler(CommandHandler("approve", self.cmd_approve))
        app.add_handler(CommandHandler("reject", self.cmd_reject))
        app.add_handler(CommandHandler("qstatus", self.cmd_qstatus))
        app.add_handler(CommandHandler("qrun", self.cmd_qrun))
        app.add_handler(CommandHandler("qlater", self.cmd_qlater))
        app.add_handler(CommandHandler("gitcommit", self.cmd_gitcommit))
        app.add_handler(CommandHandler("custom", self.cmd_custom))
        app.add_handler(CommandHandler("id", self.cmd_id))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        return app
