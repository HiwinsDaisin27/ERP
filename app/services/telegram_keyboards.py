def main_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Examples", "callback_data": "intake:examples"},
                {"text": "Daily Reports", "callback_data": "menu:reports"},
            ],
            [
                {"text": "Sites", "callback_data": "lookup:sites"},
                {"text": "Workers", "callback_data": "lookup:workers"},
            ],
            [
                {"text": "Help", "callback_data": "menu:help"},
            ],
        ]
    }


def intake_examples_text() -> str:
    return "\n\n".join(
        [
            "Send site updates as plain text. The upcoming LLM tool layer will extract the fields and call backend tools.",
            "Attendance example:\nSite A\nPresent:\nRavi\nKumar\nMani\nAbsent:\nArun",
            "Material example:\nSite A received 50 bags cement from Kumar Traders today.",
            "Expense example:\nSite A expense: transport 2500 for sand delivery today.",
            "Progress example:\nSite A progress: ground floor column shuttering completed. Notes: curing started.",
        ]
    )


def reports_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "Daily Attendance", "callback_data": "report:attendance_daily"}],
            [{"text": "Daily Site Report", "callback_data": "report:site_daily"}],
            [{"text": "Weekly Payroll", "callback_data": "report:payroll_weekly"}],
            [{"text": "Back", "callback_data": "menu:main"}],
        ]
    }
