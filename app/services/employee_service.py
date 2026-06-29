"""Employee directory with role-based visibility."""

import logging
from datetime import date
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload

from app.db.models import Employee, User
from app.db.session import get_session

logger = logging.getLogger(__name__)

ACCESS_ROLES_ALL = frozenset({"hr", "executive"})
ACCESS_ROLE_MANAGER = "manager"


def _employee_to_dict(employee: Employee) -> dict[str, Any]:
    """Serialize an employee ORM record."""
    start = employee.start_date
    return {
        "employee_id": employee.employee_id,
        "name": employee.name,
        "department": employee.department,
        "role": employee.job_title,
        "job_title": employee.job_title,
        "email": employee.email,
        "location": employee.location or "",
        "manager": employee.manager.name if employee.manager else "",
        "manager_employee_id": employee.manager_employee_id,
        "access_role": employee.access_role,
        "start_date": start.isoformat() if isinstance(start, date) else str(start or ""),
        "status": employee.status,
    }


def get_employee_record(employee_id: str) -> dict[str, Any] | None:
    """Fetch one employee by ID."""
    with get_session() as session:
        employee = session.scalar(
            select(Employee)
            .options(joinedload(Employee.manager))
            .where(Employee.employee_id == employee_id.upper())
        )
        if not employee:
            return None
        return _employee_to_dict(employee)


def get_employee_for_user(user: User) -> dict[str, Any] | None:
    """Resolve the employee record linked to a user account."""
    with get_session() as session:
        employee: Employee | None = None
        if user.employee_id:
            employee = session.scalar(
                select(Employee)
                .options(joinedload(Employee.manager))
                .where(Employee.employee_id == user.employee_id)
            )
        if not employee:
            employee = session.scalar(
                select(Employee)
                .options(joinedload(Employee.manager))
                .where(Employee.email == user.email.lower())
            )
            if employee and not user.employee_id:
                db_user = session.get(User, user.id)
                if db_user:
                    db_user.employee_id = employee.employee_id
        if not employee:
            return None
        return _employee_to_dict(employee)


def _visible_employee_ids(session, viewer: Employee) -> set[str] | None:
    """Return visible employee IDs, or None if the viewer can see everyone."""
    if viewer.access_role in ACCESS_ROLES_ALL:
        return None

    if viewer.access_role == ACCESS_ROLE_MANAGER:
        report_ids = session.scalars(
            select(Employee.employee_id).where(
                Employee.manager_employee_id == viewer.employee_id
            )
        ).all()
        return {viewer.employee_id, *report_ids}

    return {viewer.employee_id}


def list_all_employees(search: str | None = None) -> list[dict[str, Any]]:
    """List every employee (used when no user context is available)."""
    with get_session() as session:
        query = select(Employee).options(joinedload(Employee.manager)).order_by(Employee.name)
        if search:
            lowered = f"%{search.lower()}%"
            query = query.where(
                or_(
                    Employee.name.ilike(lowered),
                    Employee.employee_id.ilike(lowered),
                    Employee.email.ilike(lowered),
                    Employee.department.ilike(lowered),
                )
            )
        employees = session.scalars(query).unique().all()
        return [_employee_to_dict(employee) for employee in employees]


def list_visible_employees(user: User, search: str | None = None) -> list[dict[str, Any]]:
    """List employees visible to the signed-in user based on org hierarchy."""
    with get_session() as session:
        viewer = None
        if user.employee_id:
            viewer = session.get(Employee, user.employee_id)
        if not viewer:
            viewer = session.scalar(select(Employee).where(Employee.email == user.email.lower()))

        if not viewer:
            logger.info("No employee record for user %s — returning empty directory", user.email)
            return []

        allowed_ids = _visible_employee_ids(session, viewer)
        query = select(Employee).options(joinedload(Employee.manager)).order_by(Employee.name)

        if allowed_ids is not None:
            query = query.where(Employee.employee_id.in_(allowed_ids))

        if search:
            lowered = f"%{search.lower()}%"
            query = query.where(
                or_(
                    Employee.name.ilike(lowered),
                    Employee.employee_id.ilike(lowered),
                    Employee.email.ilike(lowered),
                    Employee.department.ilike(lowered),
                )
            )

        employees = session.scalars(query).unique().all()
        return [_employee_to_dict(employee) for employee in employees]


def can_view_employee(viewer: User, target_employee_id: str) -> bool:
    """Return True if the viewer may access the target employee record."""
    visible = list_visible_employees(viewer)
    return any(employee["employee_id"] == target_employee_id.upper() for employee in visible)


def get_access_role_label(access_role: str) -> str:
    """Human-readable label for an access role."""
    labels = {
        "executive": "Executive",
        "hr": "HR",
        "manager": "Manager",
        "employee": "Employee",
    }
    return labels.get(access_role, "Workspace member")
