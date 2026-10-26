def test_register_rejects_empty_payload(client):
    response = client.post("/api/v1/users/register", json={})

    assert response.status_code == 422


def test_unknown_route_returns_not_found(client):
    response = client.get("/api/v1/route-that-does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "NOT_FOUND"


def test_wrong_method_returns_method_not_allowed(client):
    response = client.post("/health")

    assert response.status_code == 405
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "METHOD_NOT_ALLOWED"

def test_register_rejects_invalid_email(client):
    response = client.post("/api/v1/users/register", json={"name": "Test User", "email": "not-an-email", "password": "StrongPass123"})
    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post("/api/v1/users/register", json={"name": "Test User", "email": "shortpass@example.com", "password": "123"})
    assert response.status_code == 422


def test_duplicate_registration_is_rejected(client):
    payload = {"name": "Duplicate User", "email": "duplicate@example.com", "password": "StrongPass123"}
    first = client.post("/api/v1/users/register", json=payload)
    second = client.post("/api/v1/users/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


def test_login_rejects_unknown_user(client):
    response = client.post("/api/v1/users/login", json={"email": "missing@example.com", "password": "WrongPass123"})
    assert response.status_code == 401


def test_refresh_rejects_invalid_token(client):
    response = client.post("/api/v1/users/refresh", json={"refresh_token": "invalid-token"})
    assert response.status_code == 401


def test_email_verification_rejects_invalid_token(client):
    response = client.get("/api/v1/users/verify-email", params={"token": "invalid-token"})
    assert response.status_code == 400


def test_login_rejects_invalid_password(client):
    registration = client.post(
        "/api/v1/users/register",
        json={
            "name": "Password Test",
            "email": "wrongpass@example.com",
            "password": "StrongPass123"
        }
    )
    assert registration.status_code == 201

    response = client.post(
        "/api/v1/users/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPass123"
        }
    )
    assert response.status_code == 401


def create_test_user(db_session, email, role="user"):
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        name="RBAC Test User",
        email=email,
        password_hash=hash_password("StrongPass123"),
        role=role,
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_admin_endpoint_rejects_unauthenticated_request(client):
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401


def test_admin_endpoint_rejects_regular_user(client, db_session):
    from app.core.security import create_access_token

    user = create_test_user(db_session, "regular-rbac@example.com")
    token = create_access_token(str(user.id))

    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_endpoint_allows_admin(client, db_session):
    from app.core.security import create_access_token

    admin = create_test_user(db_session, "admin-rbac@example.com", role="admin")
    token = create_access_token(str(admin.id))

    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert any(user["email"] == "admin-rbac@example.com" for user in response.json())


from uuid import uuid4

def create_test_category(db_session):
    from app.models.category import Category

    category = Category(
        name=f"Test Category {uuid4().hex[:12]}",
        description="Category for automated tests",
    )
    db_session.add(category)
    db_session.flush()
    db_session.refresh(category)
    return category

def create_published_test_blog(db_session, author_id):
    from app.models.blog import Blog

    category = create_test_category(db_session)
    blog = Blog(
        title="Automated Test Blog",
        content="Content for automated testing.",
        category_id=category.id,
        author_id=author_id,
        is_published=True,
    )
    db_session.add(blog)
    db_session.commit()
    db_session.refresh(blog)
    return blog


def test_blog_create_and_get(client, db_session):
    from app.core.security import create_access_token

    user = create_test_user(db_session, "blog-create@example.com")
    category = create_test_category(db_session)
    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

    created = client.post(
        "/api/v1/blogs/",
        headers=headers,
        json={
            "title": "My Test Blog",
            "content": "Test blog content",
            "category_id": category.id,
        },
    )
    assert created.status_code == 201
    blog_id = created.json()["id"]

    fetched = client.get(f"/api/v1/blogs/{blog_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "My Test Blog"


def test_blog_update(client, db_session):
    from app.core.security import create_access_token

    user = create_test_user(db_session, "blog-update@example.com")
    blog = create_published_test_blog(db_session, user.id)
    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

    response = client.patch(
        f"/api/v1/blogs/{blog.id}",
        headers=headers,
        json={"title": "Updated Test Blog"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Test Blog"


def test_admin_can_publish_blog(client, db_session):
    from app.core.security import create_access_token
    from app.models.blog import Blog

    admin = create_test_user(db_session, "blog-publish-admin@example.com", role="admin")
    blog = create_published_test_blog(db_session, admin.id)
    blog.is_published = False
    db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(str(admin.id))}"}
    response = client.patch(
        f"/api/v1/blogs/{blog.id}/publish",
        headers=headers,
        json={"is_published": True},
    )
    assert response.status_code == 200
    assert response.json()["is_published"] is True


def test_admin_can_delete_blog(client, db_session):
    from app.core.security import create_access_token
    from app.models.blog import Blog

    admin = create_test_user(db_session, "blog-delete-admin@example.com", role="admin")
    blog = create_published_test_blog(db_session, admin.id)
    headers = {"Authorization": f"Bearer {create_access_token(str(admin.id))}"}

    response = client.delete(f"/api/v1/blogs/{blog.id}", headers=headers)
    assert response.status_code == 204
    assert db_session.get(Blog, blog.id) is None


def test_create_comment(client, db_session):
    from app.core.security import create_access_token

    user = create_test_user(db_session, "comment-create@example.com")
    blog = create_published_test_blog(db_session, user.id)
    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

    response = client.post(
        f"/api/v1/blogs/{blog.id}/comments",
        headers=headers,
        json={"content": "My test comment"},
    )
    assert response.status_code == 201
    assert response.json()["content"] == "My test comment"


def test_user_can_update_own_comment(client, db_session):
    from app.core.security import create_access_token
    from app.models.comment import Comment

    user = create_test_user(db_session, "comment-owner@example.com")
    blog = create_published_test_blog(db_session, user.id)
    comment = Comment(blog_id=blog.id, user_id=user.id, content="Original comment")
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
    response = client.put(
        f"/api/v1/blogs/{blog.id}/comments/{comment.id}",
        headers=headers,
        json={"content": "Updated comment"},
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated comment"


def test_user_cannot_update_another_users_comment(client, db_session):
    from app.core.security import create_access_token
    from app.models.comment import Comment

    owner = create_test_user(db_session, "comment-real-owner@example.com")
    other_user = create_test_user(db_session, "comment-other-user@example.com")
    blog = create_published_test_blog(db_session, owner.id)
    comment = Comment(blog_id=blog.id, user_id=owner.id, content="Owner comment")
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    headers = {"Authorization": f"Bearer {create_access_token(str(other_user.id))}"}
    response = client.put(
        f"/api/v1/blogs/{blog.id}/comments/{comment.id}",
        headers=headers,
        json={"content": "Unauthorized edit"},
    )
    assert response.status_code == 403


def test_user_can_delete_own_comment(client, db_session):
    from app.core.security import create_access_token
    from app.models.comment import Comment

    user = create_test_user(db_session, "comment-delete@example.com")
    blog = create_published_test_blog(db_session, user.id)
    comment = Comment(blog_id=blog.id, user_id=user.id, content="Delete this comment")
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
    response = client.delete(
        f"/api/v1/blogs/{blog.id}/comments/{comment.id}",
        headers=headers,
    )
    assert response.status_code == 204
    assert db_session.get(Comment, comment.id) is None


def test_create_rating(client, db_session):
    from app.core.security import create_access_token

    user = create_test_user(db_session, "rating-create@example.com")
    blog = create_published_test_blog(db_session, user.id)
    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

    response = client.post(
        f"/api/v1/blogs/{blog.id}/ratings",
        headers=headers,
        json={"value": 5},
    )
    assert response.status_code == 201
    assert response.json()["value"] == 5


def test_user_can_update_own_rating(client, db_session):
    from app.core.security import create_access_token

    user = create_test_user(db_session, "rating-update@example.com")
    blog = create_published_test_blog(db_session, user.id)
    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

    created = client.post(
        f"/api/v1/blogs/{blog.id}/ratings",
        headers=headers,
        json={"value": 3},
    )
    assert created.status_code == 201

    updated = client.put(
        f"/api/v1/blogs/{blog.id}/ratings/me",
        headers=headers,
        json={"value": 4},
    )
    assert updated.status_code == 200
    assert updated.json()["value"] == 4


def test_user_cannot_rate_same_blog_twice(client, db_session):
    user = create_test_user(db_session, "rating-duplicate@example.com")
    blog = create_published_test_blog(db_session, user.id)
    from app.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
    payload = {"value": 4}

    first = client.post(
        f"/api/v1/blogs/{blog.id}/ratings",
        headers=headers,
        json=payload,
    )
    second = client.post(
        f"/api/v1/blogs/{blog.id}/ratings",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_email_verification_succeeds(client, db_session):
    from app.core.email_verification import create_verification_token
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        name="Verify Test User",
        email="verify-success@example.com",
        password_hash=hash_password("StrongPass123"),
        role="user",
        email_verified=False,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_verification_token(user.id, user.email)
    response = client.get("/api/v1/users/verify-email", params={"token": token})

    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully"
    db_session.refresh(user)
    assert user.email_verified is True


def test_email_verification_rejects_expired_token(client):
    from itsdangerous import URLSafeTimedSerializer
    from app.core.config import settings
    from unittest.mock import patch
    import app.core.email_verification as email_verification

    serializer = URLSafeTimedSerializer(
        settings.JWT_SECRET_KEY,
        salt="user-email-verification-v1",
    )
    token = serializer.dumps(
        {"user_id": 999999, "email": "expired@example.com"}
    )

    with patch.object(
        email_verification.serializer,
        "loads",
        side_effect=__import__("itsdangerous").SignatureExpired("expired"),
    ):
        response = client.get(
            "/api/v1/users/verify-email",
            params={"token": token},
        )

    assert response.status_code == 400
    assert "expired" in str(response.json()).lower()



