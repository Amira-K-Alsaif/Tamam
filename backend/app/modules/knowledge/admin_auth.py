"""Authorization for knowledge administration endpoints."""

import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
) -> str:
    """Verify the Supabase user and require admin privileges."""

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="يجب تسجيل الدخول أولاً",
        )

    # Optional dependencies are loaded only when needed.
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(Path(__file__).resolve().parents[3] / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise HTTPException(
            status_code=503,
            detail="خدمة المصادقة غير مهيأة",
        )

    db = create_client(url, key)

    try:
        response = db.auth.get_user(credentials.credentials)
        user = response.user
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="جلسة الدخول غير صالحة",
        ) from None

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="المستخدم غير معروف",
        )

    metadata = user.app_metadata or {}

    if metadata.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="هذه العملية مخصصة للمشرف فقط",
        )

    return user.id
