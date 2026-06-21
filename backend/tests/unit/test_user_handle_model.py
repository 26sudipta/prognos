import uuid

from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus, UserHandle


def test_enum_values():
    assert HandlePlatform.CODEFORCES.value == "codeforces"
    assert HandleStatus.ACTIVE.value == "active"
    assert HandleStatus.SUSPENDED.value == "suspended"
    assert HandleSyncStatus.IDLE.value == "idle"
    assert HandleSyncStatus.IN_PROGRESS.value == "in_progress"
    assert HandleSyncStatus.COMPLETED.value == "completed"
    assert HandleSyncStatus.SYNC_ERROR.value == "sync_error"


def test_model_instantiation():
    handle = UserHandle(
        user_id=uuid.uuid4(),
        platform=HandlePlatform.CODEFORCES,
        handle="tourist",
    )
    assert handle.handle == "tourist"
    assert handle.platform == HandlePlatform.CODEFORCES
    assert handle.verification_token is None
    assert handle.last_sync_error is None
    assert handle.verified_at is None
