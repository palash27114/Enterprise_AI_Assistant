#!/usr/bin/env python3
"""Generate Liquibase SQL seed for ~100 employee org hierarchy."""

from __future__ import annotations

import json
from pathlib import Path

FIRST = [
    "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Neha", "Arjun", "Kavya",
    "Rahul", "Sneha", "Aditya", "Isha", "Karan", "Meera", "Dev", "Nisha",
    "Sanjay", "Pooja", "Manish", "Divya", "Nitin", "Ritu", "Amit", "Shreya",
    "Vivek", "Tanvi", "Gaurav", "Anjali", "Harsh", "Swati", "Yash", "Preeti",
    "Akash", "Bhavna", "Chetan", "Deepa", "Farhan", "Gita", "Hemant", "Indira",
    "James", "Kelly", "Liam", "Maya", "Noah", "Olivia", "Paul", "Quinn",
    "Ryan", "Sara", "Tom", "Uma", "Victor", "Wendy", "Xavier", "Yolanda",
    "Zoe", "Ethan", "Fiona", "George", "Hannah", "Ian", "Julia", "Kevin",
    "Laura", "Marcus", "Nina", "Oscar", "Paula", "Quentin", "Rosa", "Simon",
    "Tara", "Umar", "Vera", "Walter", "Xena", "Yusuf", "Zara", "Blake",
    "Chloe", "Derek", "Elena", "Felix", "Grace", "Henry", "Irene", "Jack",
    "Kate", "Leo", "Mila", "Nate", "Owen", "Paige", "Reed", "Sasha",
]

LAST = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Iyer", "Nair",
    "Joshi", "Mehta", "Kapoor", "Malhotra", "Chopra", "Bhatia", "Saxena", "Verma",
    "Agarwal", "Das", "Pillai", "Rao", "Khan", "Ali", "Hussain", "Fernandes",
    "D'Souza", "Pereira", "Rodrigues", "Mukherjee", "Banerjee", "Chatterjee",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson",
    "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia",
    "Martinez", "Robinson", "Clark", "Lewis", "Lee", "Walker", "Hall", "Allen",
    "Young", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson",
    "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker",
    "Evans", "Edwards", "Collins", "Stewart", "Morris", "Rogers", "Reed", "Cook",
    "Morgan", "Bell", "Murphy", "Bailey", "Rivera", "Cooper", "Richardson", "Cox",
    "Howard", "Ward", "Torres", "Peterson", "Gray", "Ramirez", "James", "Watson",
]

name_idx = 0


def next_name() -> tuple[str, str]:
    global name_idx
    first = FIRST[name_idx % len(FIRST)]
    last = LAST[name_idx % len(LAST)]
    name_idx += 1
    return first, last


def slug(first: str, last: str) -> str:
    return f"{first.lower()}.{last.lower()}@company.com"


records: list[dict] = []
emp_num = 1001


def sql_escape(value: str) -> str:
    return value.replace("'", "''")


def add(
    job_title: str,
    department: str,
    manager_id: str | None,
    access_role: str,
    location: str = "Bangalore",
    fixed_name: tuple[str, str] | None = None,
    fixed_email: str | None = None,
) -> str:
    global emp_num
    emp_id = f"EMP-{emp_num}"
    if fixed_name:
        first, last = fixed_name
    else:
        first, last = next_name()
    email = fixed_email or slug(first, last)
    records.append(
        {
            "employee_id": emp_id,
            "name": f"{first} {last}",
            "department": department,
            "job_title": job_title,
            "email": email,
            "location": location,
            "manager_employee_id": manager_id,
            "access_role": access_role,
            "start_date": "2020-01-15",
            "status": "Active",
        }
    )
    emp_num += 1
    return emp_id


def add_many(
    count: int,
    job_title: str,
    department: str,
    manager_id: str,
    access_role: str = "employee",
    location: str = "Bangalore",
) -> list[str]:
    ids = []
    for _ in range(count):
        ids.append(add(job_title, department, manager_id, access_role, location))
    return ids


# CEO
ceo = add(
    "Chief Executive Officer",
    "Executive",
    None,
    "executive",
    fixed_name=("Riley", "Morgan"),
    fixed_email="ceo@company.com",
)

# CTO branch
cto = add("Chief Technology Officer", "Technology", ceo, "executive", fixed_name=("Arun", "Venkatesh"), fixed_email="cto@company.com")

eng_mgr = add(
    "Engineering Manager",
    "Engineering",
    cto,
    "manager",
    fixed_name=("Jane", "Doe"),
    fixed_email="jane.doe@company.com",
)
add_many(3, "Senior Software Engineer", "Engineering", eng_mgr)
add(
    "Senior Software Engineer",
    "Engineering",
    eng_mgr,
    "employee",
    fixed_name=("Palash", "Joshi"),
    fixed_email="palash.joshi@company.com",
)
add_many(8, "Software Engineer", "Engineering", eng_mgr)
add_many(4, "Junior Software Engineer", "Engineering", eng_mgr)
qa_lead = add("QA Lead", "Engineering", eng_mgr, "manager")
add_many(3, "QA Engineer", "Engineering", qa_lead)
add_many(2, "DevOps Engineer", "Engineering", eng_mgr)
add_many(2, "UI/UX Designer", "Engineering", eng_mgr)

it_mgr = add("IT Manager", "IT", cto, "manager", fixed_name=("Suresh", "Menon"), fixed_email="it.manager@company.com")
add_many(2, "System Administrator", "IT", it_mgr)
add("Network Engineer", "IT", it_mgr, "employee")
add_many(3, "IT Support Engineer", "IT", it_mgr)

# COO branch
coo = add("Chief Operating Officer", "Operations", ceo, "executive", fixed_name=("Lakshmi", "Narayanan"), fixed_email="coo@company.com")

ops_mgr = add("Operations Manager", "Operations", coo, "manager")
add_many(4, "Operations Executive", "Operations", ops_mgr)
add_many(2, "Office Administrator", "Operations", ops_mgr)

cs_mgr = add(
    "Customer Success Manager",
    "Customer Success",
    coo,
    "manager",
    fixed_name=("Sam", "Wilson"),
    fixed_email="sam.wilson@company.com",
)
add_many(4, "Customer Success Executive", "Customer Success", cs_mgr)
add(
    "Customer Success Executive",
    "Customer Success",
    cs_mgr,
    "employee",
    fixed_name=("Maria", "Garcia"),
    fixed_email="maria.garcia@company.com",
)
add_many(4, "Support Engineer", "Customer Success", cs_mgr)

# CFO branch
cfo = add("Chief Financial Officer", "Finance", ceo, "executive", fixed_name=("Anita", "Desai"), fixed_email="cfo@company.com")
fin_mgr = add("Finance Manager", "Finance", cfo, "manager")
add_many(3, "Accountant", "Finance", fin_mgr)
add("Payroll Specialist", "Finance", fin_mgr, "employee")
add_many(2, "Finance Analyst", "Finance", fin_mgr)

# CHRO branch
chro = add(
    "HR Director",
    "HR",
    ceo,
    "hr",
    fixed_name=("Alex", "Chen"),
    fixed_email="alex.chen@company.com",
)
hr_mgr = add("HR Manager", "HR", chro, "hr")
add_many(3, "HR Executive", "HR", hr_mgr, "hr")
add_many(2, "Recruiter", "HR", hr_mgr, "employee")
add("Learning & Development Specialist", "HR", hr_mgr, "employee")
add("HR Operations Executive", "HR", hr_mgr, "employee")

# Sales branch
sales_dir = add("Sales Director", "Sales", ceo, "executive", fixed_name=("David", "Foster"), fixed_email="sales.director@company.com")
sales_mgr_1 = add("Sales Manager", "Sales", sales_dir, "manager")
sales_mgr_2 = add("Sales Manager", "Sales", sales_dir, "manager")
add_many(2, "Senior Sales Executive", "Sales", sales_mgr_1)
add_many(2, "Senior Sales Executive", "Sales", sales_mgr_2)
add_many(4, "Sales Executive", "Sales", sales_mgr_1)
add_many(4, "Sales Executive", "Sales", sales_mgr_2)
add_many(2, "Sales Development Representative", "Sales", sales_mgr_1)
add_many(2, "Sales Development Representative", "Sales", sales_mgr_2)

# Marketing branch
mkt_dir = add("Marketing Director", "Marketing", ceo, "executive", fixed_name=("Emily", "Carter"), fixed_email="marketing.director@company.com")
mkt_mgr = add("Marketing Manager", "Marketing", mkt_dir, "manager")
add_many(2, "Digital Marketing Specialist", "Marketing", mkt_mgr)
add_many(2, "Content Writer", "Marketing", mkt_mgr)
add("Graphic Designer", "Marketing", mkt_mgr, "employee")
add("SEO Specialist", "Marketing", mkt_mgr, "employee")
add("Social Media Executive", "Marketing", mkt_mgr, "employee")

# Pad to 100 if under
while len(records) < 100:
    add("Business Analyst", "Operations", ops_mgr, "employee")

print(f"Generated {len(records)} employees")

values_sql = []
for r in records:
    mgr = f"'{r['manager_employee_id']}'" if r["manager_employee_id"] else "NULL"
    values_sql.append(
        f"    ('{r['employee_id']}', '{sql_escape(r['name'])}', '{sql_escape(r['department'])}', "
        f"'{sql_escape(r['job_title'])}', '{sql_escape(r['email'])}', '{sql_escape(r['location'])}', {mgr}, "
        f"'{r['access_role']}', '{r['start_date']}', '{r['status']}')"
    )

sql = """--liquibase formatted sql

--changeset enterprise-ai:003-seed-org-hierarchy
INSERT INTO employees (employee_id, name, department, job_title, email, location, manager_employee_id, access_role, start_date, status)
VALUES
"""
sql += ",\n".join(values_sql)
sql += """
ON CONFLICT (employee_id) DO UPDATE SET
    name = EXCLUDED.name,
    department = EXCLUDED.department,
    job_title = EXCLUDED.job_title,
    email = EXCLUDED.email,
    location = EXCLUDED.location,
    manager_employee_id = EXCLUDED.manager_employee_id,
    access_role = EXCLUDED.access_role,
    start_date = EXCLUDED.start_date,
    status = EXCLUDED.status;

--changeset enterprise-ai:003-link-users-by-email
UPDATE users u
SET employee_id = e.employee_id
FROM employees e
WHERE LOWER(u.email) = LOWER(e.email);
"""

out = Path(__file__).resolve().parents[1] / "db/changelog/changesets/003-seed-org-hierarchy.sql"
out.write_text(sql, encoding="utf-8")
print(f"Wrote {out}")

# Also write JSON for reference
ref = Path(__file__).resolve().parents[1] / "app/data/org_employees.json"
ref.write_text(json.dumps(records, indent=2), encoding="utf-8")
