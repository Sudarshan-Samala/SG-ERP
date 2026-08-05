PERMISSIONS = {
    "rbac.manage": "Manage tenant roles and user role assignments",
    "students.read": "View student records", "students.create": "Create student records", "students.manage": "Update and remove student records",
    "admissions.read": "View admission enquiries", "admissions.manage": "Create and manage admission enquiries",
    "attendance.read": "View student attendance", "attendance.mark": "Mark student attendance",
    "fees.read": "View fee types, structures, invoices and payments", "fees.manage": "Manage fee types and fee structures", "fees.invoice.create": "Create student fee invoices", "fees.payment.collect": "Record fee payments",
    "hr.employee.read": "View employees", "hr.employee.create": "Create employees", "hr.salary.read": "View salary structures", "hr.salary.manage": "Manage salary structures", "hr.payroll.read": "View payroll", "hr.payroll.create": "Create payroll records",
    "exam.read": "View examinations and schedules", "exam.manage": "Manage examinations and exam types", "exam.schedule.manage": "Manage examination schedules", "exam.result.read": "View examination results", "exam.result.create": "Create examination results",
    "inventory.read": "View inventory", "inventory.manage": "Manage inventory", "assets.read": "View assets", "assets.manage": "Manage assets",
    "transport.read": "View transport vehicles, routes and drivers", "transport.manage": "Manage transport vehicles, routes and drivers",
    "helpdesk.read": "View helpdesk tickets", "helpdesk.ticket.create": "Create helpdesk tickets",
}

ROLE_PERMISSION_SETS = {
    "ERP Admin": set(PERMISSIONS),
    "Admissions Officer": {"admissions.read", "admissions.manage", "students.read", "students.create"},
    "Teacher": {"students.read", "attendance.read", "attendance.mark", "exam.read", "exam.result.read"},
    "Student Records Manager": {"students.read", "students.create", "students.manage", "admissions.read"},
    "Finance Manager": {"fees.read", "fees.manage", "fees.invoice.create", "fees.payment.collect"},
    "HR Manager": {"hr.employee.read", "hr.employee.create", "hr.salary.read", "hr.salary.manage", "hr.payroll.read", "hr.payroll.create"},
    "Exam Manager": {"exam.read", "exam.manage", "exam.schedule.manage", "exam.result.read", "exam.result.create"},
    "Asset Manager": {"inventory.read", "inventory.manage", "assets.read", "assets.manage"},
    "Transport Manager": {"transport.read", "transport.manage"},
    "Helpdesk User": {"helpdesk.read", "helpdesk.ticket.create"},
}
