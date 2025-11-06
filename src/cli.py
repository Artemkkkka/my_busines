import os
import sys
import asyncio
import traceback
import typer

app = typer.Typer(add_completion=False, help="Management commands")


def _mask(value: str | None, keep: int = 4) -> str:
    if not value:
        return ""
    return ("*" * max(0, len(value) - keep)) + value[-keep:]


@app.command("ping")
def ping():
    """Быстрый тест, что исполняется именно этот модуль."""
    typer.echo(f"OK: module file = {__file__}")


@app.command("create-superuser")
def create_superuser(
    email: str | None = typer.Option(None, "--email", "-e", help="Email суперпользователя"),
    password: str | None = typer.Option(None, "--password", "-p",
                                        help="Пароль; если не задан, спросим",
                                        prompt=False, hide_input=True),
    no_input: bool = typer.Option(False, "--no-input", help="Не задавать вопросы"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
):
    if verbose:
        db_url = os.getenv("DATABASE_URL") or os.getenv("DB_DSN") or ""
        typer.echo(f"CLI file: {__file__}")
        typer.echo(f"Python: {sys.version.split()[0]}")
        typer.echo(f"DATABASE_URL: {_mask(db_url, keep=6)}")

    if not email:
        if no_input:
            typer.echo("Ошибка: укажи --email с --no-input", err=True)
            raise typer.Exit(2)
        email = typer.prompt("Email")

    if password is None:
        if no_input:
            typer.echo("Ошибка: укажи --password с --no-input", err=True)
            raise typer.Exit(2)
        password = typer.prompt("Пароль", hide_input=True, confirmation_prompt=True)

    try:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass

        from fastapi_users.exceptions import UserAlreadyExists
        from src.users.actions.create_user import create_user
    except Exception as e:
        typer.secho("Ошибка при импорте зависимостей:", fg=typer.colors.RED)
        typer.echo("".join(traceback.format_exception(e)))
        raise typer.Exit(1)
    try:
        if verbose:
            typer.echo(f"→ Создаю суперпользователя: {email}")
        user = asyncio.run(create_user(email=email, password=password, is_superuser=True))
    except UserAlreadyExists:
        typer.secho(f"Пользователь {email} уже существует", fg=typer.colors.YELLOW)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho("Ошибка при создании пользователя:", fg=typer.colors.RED)
        typer.echo("".join(traceback.format_exception(e)))
        raise typer.Exit(1)
    uid = getattr(user, "id", None)
    typer.secho(
        f"Суперпользователь создан: {email}" + (f" (id={uid})" if uid else ""),
        fg=typer.colors.GREEN,
    )


def main():
    app()


if __name__ == "__main__":
    main()
