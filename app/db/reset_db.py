import argparse

from sqlalchemy import text

from app.db.session import engine


OPERATIONAL_TABLES = [
    "assistant_chat_messages",
    "payroll_audit_log",
    "payroll_payments",
    "payroll_line_items",
    "payroll_periods",
    "telegram_data_submissions",
    "telegram_notification_logs",
    "telegram_workflow_sessions",
    "telegram_messages",
    "telegram_users",
    "progress_updates",
    "payments",
    "payroll_runs",
    "expenses",
    "material_transactions",
    "materials",
    "site_assignments",
    "attendance",
    "employees",
    "sites",
]

USER_TABLES = [
    "web_users",
]

CONFIRM_PHRASE = "RESET_THESECOND_DATABASE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely clear TheSecond database tables for local or production maintenance."
    )
    parser.add_argument(
        "--include-users",
        action="store_true",
        help="Also delete website users/admins. Omit this to preserve login access.",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Required when running against a production database.",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help=f"Required confirmation phrase: {CONFIRM_PHRASE}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the tables that would be truncated without changing data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tables = [*OPERATIONAL_TABLES, *(USER_TABLES if args.include_users else [])]

    print("Database reset target tables:")
    for table in tables:
        print(f" - {table}")

    if not args.include_users:
        print("\nWebsite users will be preserved. Use --include-users only if you want a true zero-user wipe.")

    if args.dry_run:
        print("\nDry run only. No data changed.")
        return

    if not args.production:
        raise SystemExit("Refusing to reset without --production. Add it when you intentionally target the configured DB.")

    if args.confirm != CONFIRM_PHRASE:
        raise SystemExit(f"Refusing to reset. Pass --confirm {CONFIRM_PHRASE}")

    table_sql = ", ".join(tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {table_sql} RESTART IDENTITY CASCADE"))

    print("\nDatabase reset complete.")


if __name__ == "__main__":
    main()
