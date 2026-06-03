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


def hr_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "Add Worker", "callback_data": "hr:add_worker"}],
            [{"text": "Mark Attendance", "callback_data": "hr:attendance"}],
            [{"text": "Assign Workers", "callback_data": "hr:assign_workers"}],
            [{"text": "Back", "callback_data": "menu:main"}],
        ]
    }


def site_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "Add Site", "callback_data": "site:add_site"}],
            [{"text": "Add Material", "callback_data": "site:add_material"}],
            [{"text": "Receive Material", "callback_data": "site:receive_material"}],
            [{"text": "Consume Material", "callback_data": "site:consume_material"}],
            [{"text": "Add Expense", "callback_data": "site:add_expense"}],
            [{"text": "Progress Update", "callback_data": "site:progress_update"}],
            [{"text": "Back", "callback_data": "menu:main"}],
        ]
    }


def reports_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "Daily Attendance", "callback_data": "report:attendance_daily"}],
            [{"text": "Daily Site Report", "callback_data": "report:site_daily"}],
            [{"text": "Weekly Payroll", "callback_data": "report:payroll_weekly"}],
            [{"text": "Back", "callback_data": "menu:main"}],
        ]
    }
