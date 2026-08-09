from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.authorization_policy import AuthorizationPolicy


def make_user(*, superuser=False, permissions=(), organization_id=None, branches=()):
    class Permission:
        def __init__(self, name):
            self.name = name

    class Role:
        def __init__(self, organization_id, permissions):
            self.organization_id = organization_id
            self.permissions = [Permission(name) for name in permissions]

    class Branch:
        def __init__(self, branch_id, organization_id):
            self.id = branch_id
            self.organization_id = organization_id

    class User:
        pass

    user = User()
    user.is_superuser = superuser
    user.organization_id = organization_id or uuid4()
    user.roles = [Role(user.organization_id, permissions)]
    user.branches = [Branch(branch_id, user.organization_id) for branch_id in branches]
    return user


def test_permission_is_default_deny():
    user = make_user(permissions=["students.read"])
    assert AuthorizationPolicy.allows(user, "students.read")
    assert not AuthorizationPolicy.allows(user, "students.manage")
    with pytest.raises(HTTPException) as exc:
        AuthorizationPolicy.require(user, "students.manage")
    assert exc.value.status_code == 403


def test_tenant_scoping_denies_cross_tenant_access():
    tenant_a = uuid4()
    tenant_b = uuid4()
    user = make_user(organization_id=tenant_a, permissions=["branches.read"])
    with pytest.raises(HTTPException) as exc:
        AuthorizationPolicy.require_tenant(user, tenant_b)
    assert exc.value.status_code == 403


def test_branch_scope_denies_unassigned_branch():
    tenant = uuid4()
    allowed = uuid4()
    denied = uuid4()
    user = make_user(organization_id=tenant, permissions=["students.read"], branches=[allowed])
    AuthorizationPolicy.require_branch(None, user, allowed)
    with pytest.raises(HTTPException) as exc:
        AuthorizationPolicy.require_branch(None, user, denied)
    assert exc.value.status_code == 403


def test_superuser_is_platform_override():
    user = make_user(superuser=True)
    assert AuthorizationPolicy.allows(user, "anything.at.all")
