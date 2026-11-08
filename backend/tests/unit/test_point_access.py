from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.application.identity import IdentityService
from app.domain.identity import IdentityError, Role


@pytest.mark.parametrize(
    ("role", "assigned", "authorized"),
    [(Role.OPERADOR, True, True), (Role.OPERADOR, False, False), (Role.USUARIO, True, False)],
)
def test_point_access_requires_role_and_assignment(role, assigned, authorized):
    actor_id, point_id = uuid4(), uuid4()
    service = IdentityService.__new__(IdentityService)
    service.store = SimpleNamespace(
        has_active_assignment=lambda user, point: assigned and (user, point) == (actor_id, point_id)
    )
    actor = {"id": actor_id, "role": role.value}
    allowed_roles = frozenset({Role.OPERADOR})

    if authorized:
        service.require_point_access(actor, point_id, allowed_roles)
    else:
        with pytest.raises(IdentityError) as denied:
            service.require_point_access(actor, point_id, allowed_roles)
        assert denied.value.status == 403
        assert denied.value.code == "PUNTO_NO_AUTORIZADO"
