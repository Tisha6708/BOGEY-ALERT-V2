from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.models.role_policy import RolePolicy
from app.schemas.role_policy import (
    RolePolicyCreate,
    RolePolicyRead,
    RolePolicyUpdate,
)
from app.services.policy_service import (
    create_policy,
    deactivate_policy,
    get_all_policies,
    get_policy_by_id,
    update_policy,
)


router = APIRouter(
    prefix="/policies",
    tags=["Role Policies"],
)


# ---------------------------------------------------------
# CREATE POLICY
# ---------------------------------------------------------

@router.post(
    "/",
    response_model=RolePolicyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_role_policy(
    policy_data: RolePolicyCreate,
    session: Session = Depends(get_session),
):
    try:
        return create_policy(
            policy_data=policy_data,
            session=session,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


# ---------------------------------------------------------
# GET ALL POLICIES
# ---------------------------------------------------------

@router.get(
    "/",
    response_model=list[RolePolicyRead],
)
def list_role_policies(
    session: Session = Depends(get_session),
):
    return get_all_policies(
        session=session,
    )


# ---------------------------------------------------------
# GET POLICY BY ID
# ---------------------------------------------------------

@router.get(
    "/{policy_id}",
    response_model=RolePolicyRead,
)
def get_role_policy(
    policy_id: int,
    session: Session = Depends(get_session),
):
    policy = get_policy_by_id(
        policy_id=policy_id,
        session=session,
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role policy not found.",
        )

    return policy


# ---------------------------------------------------------
# UPDATE POLICY
# ---------------------------------------------------------

@router.put(
    "/{policy_id}",
    response_model=RolePolicyRead,
)
def update_role_policy(
    policy_id: int,
    policy_data: RolePolicyUpdate,
    session: Session = Depends(get_session),
):
    policy = get_policy_by_id(
        policy_id=policy_id,
        session=session,
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role policy not found.",
        )

    return update_policy(
        policy=policy,
        policy_data=policy_data,
        session=session,
    )


# ---------------------------------------------------------
# DEACTIVATE POLICY
# ---------------------------------------------------------

@router.delete(
    "/{policy_id}",
    response_model=RolePolicyRead,
)
def deactivate_role_policy(
    policy_id: int,
    session: Session = Depends(get_session),
):
    policy = get_policy_by_id(
        policy_id=policy_id,
        session=session,
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role policy not found.",
        )

    return deactivate_policy(
        policy=policy,
        session=session,
    )