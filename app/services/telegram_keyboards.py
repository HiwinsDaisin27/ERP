def main_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "HR Operations", "callback_data": "menu:hr"},
                {"text": "Site & Procurement", "callback_data": "menu:site"},
            ],
            [
                {"text": "Reports", "callback_data": "menu:reports"},
                {"text": "Help", "callback_data": "menu:help"},
            ],
        ]
    }


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
            [{"text": "Receive Material", "callback_data": "site:receive_material"}],
            [{"text": "Consume Material", "callback_data": "site:consume_material"}],
            [{"text": "Add Expense", "callback_data": "site:add_expense"}],
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

