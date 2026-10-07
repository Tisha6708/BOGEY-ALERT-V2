from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.role_policy import RolePolicy
from app.schemas.role_policy import (
    RolePolicyCreate,
    RolePolicyUpdate,
)


def get_policy_by_role(
    role: str,
    session: Session,
) -> RolePolicy | None:
    """
    Retrieve the active policy assigned to a role.
    """

    return session.exec(
        select(RolePolicy).where(
            RolePolicy.role == role,
            RolePolicy.is_active == True,
        )
    ).first()


def get_policy_by_id(
    policy_id: int,
    session: Session,
) -> RolePolicy | None:
    """
    Retrieve a role policy by its database ID.
    """

    return session.get(
        RolePolicy,
        policy_id,
    )


def get_all_policies(
    session: Session,
) -> list[RolePolicy]:
    """
    Retrieve all role policies.
    """

    return session.exec(
        select(RolePolicy).order_by(RolePolicy.role)
    ).all()


def create_policy(
    policy_data: RolePolicyCreate,
    session: Session,
) -> RolePolicy:
    """
    Create a new role policy.

    A role can have only one policy because RolePolicy.role
    is unique.
    """

    existing_policy = session.exec(
        select(RolePolicy).where(
            RolePolicy.role == policy_data.role
        )
    ).first()

    if existing_policy:
        raise ValueError(
            f"A policy already exists for role '{policy_data.role}'."
        )

    policy = RolePolicy(
        role=policy_data.role,
        description=policy_data.description,
        allowed_activities=policy_data.allowed_activities,
        sensitive_data_access_allowed=(
            policy_data.sensitive_data_access_allowed
        ),
        max_data_volume_per_window=(
            policy_data.max_data_volume_per_window
        ),
        max_sensitive_events_per_window=(
            policy_data.max_sensitive_events_per_window
        ),
        working_hours_start=policy_data.working_hours_start,
        working_hours_end=policy_data.working_hours_end,
        weekend_activity_allowed=(
            policy_data.weekend_activity_allowed
        ),
        is_active=True,
    )

    session.add(policy)
    session.commit()
    session.refresh(policy)

    return policy


def update_policy(
    policy: RolePolicy,
    policy_data: RolePolicyUpdate,
    session: Session,
) -> RolePolicy:
    """
    Update an existing role policy.

    Only fields supplied by the caller are changed.
    """

    update_data = policy_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            policy,
            field,
            value,
        )

    policy.updated_at = datetime.now(timezone.utc)

    session.add(policy)
    session.commit()
    session.refresh(policy)

    return policy


def deactivate_policy(
    policy: RolePolicy,
    session: Session,
) -> RolePolicy:
    """
    Deactivate a role policy without deleting it.

    Historical policy information is preserved.
    """

    policy.is_active = False
    policy.updated_at = datetime.now(timezone.utc)

    session.add(policy)
    session.commit()
    session.refresh(policy)

    return policy