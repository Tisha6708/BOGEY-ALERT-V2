import hashlib
import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.device import Device


bearer_scheme = HTTPBearer()


def hash_credential(credential: str) -> str:
    return hashlib.sha256(
        credential.encode("utf-8")
    ).hexdigest()


def verify_device_credential(
    supplied_credential: str,
    stored_hash: str
) -> bool:
    supplied_hash = hash_credential(
        supplied_credential
    )

    return hmac.compare_digest(
        supplied_hash,
        stored_hash
    )


def get_authenticated_device(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    session: Session = Depends(get_session)
) -> Device:

    token = credentials.credentials

    devices = session.exec(
        select(Device)
    ).all()

    authenticated_device = None

    for device in devices:
        if verify_device_credential(
            token,
            device.credential_hash
        ):
            authenticated_device = device
            break

    if not authenticated_device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credential"
        )

    if not authenticated_device.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is inactive"
        )

    return authenticated_device