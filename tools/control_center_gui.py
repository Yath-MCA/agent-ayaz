import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

ROOT = Path(__file__).resolve().parents[1]
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)


def _open_cmd(command_line: str) -> None:
    subprocess.Popen(
        ["cmd", "/k", command_line],
        cwd=str(ROOT),
        creationflags=CREATE_NEW_CONSOLE,
    )


def run_script(script_name: str) -> None:
    script_path = ROOT / script_name
    if not script_path.exists():
        messagebox.showerror("Missing file", f"Script not found:\n{script_path}")
        return

    _open_cmd(f'"{script_path}"')


def run_python(command: str, title: str) -> None:
    _open_cmd(f'"c:/python313/python.exe" {command}')


def main() -> None:
    app = tk.Tk()
    app.title("AyazDy Control Center")
    app.geometry("620x520")
    app.resizable(False, False)

    title = tk.Label(app, text="AyazDy Control Center", font=("Segoe UI", 18, "bold"))
    title.pack(pady=(16, 6))

    subtitle = tk.Label(
        app,
        text="Click a button to run start/build/deploy scripts in a new terminal window.",
        font=("Segoe UI", 10),
    )
    subtitle.pack(pady=(0, 14))

    container = tk.Frame(app)
    container.pack(fill="both", expand=True, padx=20, pady=8)

    buttons = [
        ("Start API (start.bat)", lambda: run_script("start.bat")),
        ("Build Package (build.bat)", lambda: run_script("build.bat")),
        ("Build EXE (build-exe.bat)", lambda: run_script("build-exe.bat")),
        ("Run Production (run-production.bat)", lambda: run_script("run-production.bat")),
        ("Docker Build (docker-build.bat)", lambda: run_script("docker-build.bat")),
        ("Check LLM (check_llm.bat)", lambda: run_script("check_llm.bat")),
        ("Git GUI (ayazgitdy_gui.bat)", lambda: run_script("ayazgitdy_gui.bat")),
        ("CLI Health", lambda: run_python("-m cli.cli health", "AyazDy - CLI Health")),
        (
            "CLI Queue Status",
            lambda: run_python("-m cli.cli --key your_super_secret_key qstatus", "AyazDy - CLI Queue Status"),
        ),
    ]

    for index, (label, callback) in enumerate(buttons):
        row = index // 2
        col = index % 2
        btn = tk.Button(
            container,
            text=label,
            command=callback,
            width=34,
            height=2,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        btn.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    for col in range(2):
        container.grid_columnconfigure(col, weight=1)

    note = tk.Label(
        app,
        text=(
            "Tip: Update API key in tools/control_center_gui.py for protected CLI buttons, "
            "or use the terminal for custom keys."
        ),
        font=("Segoe UI", 9),
        fg="#555",
        wraplength=580,
        justify="center",
    )
    note.pack(pady=(10, 12))

    app.mainloop()


if __name__ == "__main__":
    main()
