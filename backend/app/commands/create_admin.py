"""Create the admin account, or reset its password.

    uv run python -m app.commands.create_admin --email you@example.com
    uv run python -m app.commands.create_admin --email you@example.com --reset-password

The password is prompted for twice (never passed as an argument, which would land in
the shell history). Without a terminal it is read from the first line of stdin.
"""

import argparse
import asyncio
import getpass
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.database import SessionLocal, engine
from app.services.auth import UserExistsError, UserNotFoundError, create_admin

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 256


def _read_password() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.readline().rstrip("\r\n")
    password = getpass.getpass("Password: ")
    if getpass.getpass("Repeat password: ") != password:
        raise SystemExit("Passwords don't match.")
    return password


async def _run(email: str, password: str, *, reset_password: bool) -> None:
    try:
        async with SessionLocal() as session:
            user = await create_admin(session, email, password, reset_password=reset_password)
            action = "Password reset for" if reset_password else "Created admin"
            print(f"{action} {user.email} (id {user.id}).")
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create the admin account or reset its password.")
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="change the password of an existing admin (also logs out every session)",
    )
    args = parser.parse_args(argv)

    try:
        email = TypeAdapter(EmailStr).validate_python(args.email)
    except ValidationError:
        raise SystemExit(f"Not a valid email address: {args.email}") from None
    password = _read_password()
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise SystemExit(
            f"The password must be {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters."
        )
    try:
        asyncio.run(_run(email, password, reset_password=args.reset_password))
    except UserExistsError:
        raise SystemExit(
            f"{email} already exists. Use --reset-password to change its password."
        ) from None
    except UserNotFoundError:
        raise SystemExit(f"No admin with the email {email}.") from None


if __name__ == "__main__":
    main()
