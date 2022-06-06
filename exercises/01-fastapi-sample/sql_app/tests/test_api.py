
def create_testuser(client, email="deadpool@example.com", 
                    password="chimichangas4life"):
    """テストユーザー追加"""
    return client.post(
        "/users/",
        json={"email": email, "password": password}
    )


def create_testitem(client, user_id, token, 
                    title="item1", desc="item1_desc"):
    """テストitem追加"""
    return client.post(
        f"/users/{user_id}/items/",
        json={"title": title, "description": desc},
        headers={'X-API-TOKEN': token}
    )


def test_create_user(test_db, client):
    user_res = create_testuser(client)
    data = user_res.json()
    assert user_res.status_code == 200, user_res.text
    assert 'user' in data
    user = data['user']
    assert user["email"] == "deadpool@example.com"
    assert "id" in user
    user_id = user["id"]

    assert 'X-API-TOKEN' in data
    token = f'FAKE_ENCODE::user_id##{user_id}'
    assert data['X-API-TOKEN'] == token


def test_login(test_db, client):
    user_res = create_testuser(client)
    created_token = user_res.json()['X-API-TOKEN']

    login_res = client.get(
        "/login/",
        params={"email": "deadpool@example.com", 
                "password": "chimichangas4life"}
    )
    data = login_res.json()

    assert login_res.status_code == 200
    assert data['login_status'] == "success"
    assert data['X-API-TOKEN'] == created_token

    # test login failure
    fail_res = client.get(
        "/login/",
        params={"email": "__fail__deadpool@example.com", 
                "password": "chimichangas4life"}
    )
    assert fail_res.status_code == 401
    assert fail_res.text == (
        """{"detail":"Incorrect username or password"}""")


def test_auth_token(test_db, client):
    user_res = create_testuser(client)
    token = user_res.json()['X-API-TOKEN']

    health_res = client.get(
        f"/health-check", headers={'X-API-TOKEN': token})
    data = health_res.json()
    assert health_res.status_code == 200
    assert data['status'] == 'ok'

    # authenticate with invalid token
    invalid_token = "invalid"
    fail_res = client.get(
        f"/health-check", headers={'X-API-TOKEN': invalid_token})
    assert fail_res.status_code == 404
    assert fail_res.text == (
        """{"detail":"User is not authenticated"}""")

    # without token
    none_res = client.get(f"/health-check")
    assert none_res.status_code == 404
    assert none_res.text == (
        """{"detail":"X-API-TOKEN is None"}""")


def test_get_user(test_db, client):
    response = create_testuser(client)
    data = response.json()
    user_id = data['user']['id']
    token = data['X-API-TOKEN']

    response = client.get(
        f"/users/{user_id}", headers={'X-API-TOKEN': token})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "deadpool@example.com"
    assert data["id"] == user_id

def test_read_my_items(test_db, client):
    user_res = create_testuser(client)
    user_data = user_res.json()
    user_id = user_data['user']['id']
    token = user_data['X-API-TOKEN']
    create_testitem(client, user_id, token)

    # 該当ユーザー外のitem追加
    create_testuser(
        client, email="dummy@", password="dummypass")
    create_testitem(
        client, 2, token, title="dummy_item", desc="dummy")

    item_res = client.get(
        f"/me/items", headers={'X-API-TOKEN': token})
    data = item_res.json()
    assert item_res.status_code == 200
    assert len(data) == 1
    assert data[0]['title'] == 'item1'
    assert data[0]['description'] == 'item1_desc'

def test_delete_user(test_db, client):
    user_res = create_testuser(client)
    user_data = user_res.json()
    user_id = user_data['user']['id']
    token = user_data['X-API-TOKEN']
    create_testitem(client, user_id, token)

    # 削除ユーザーとitem追加
    del_user_res = create_testuser(
        client, email="deluser@", password="deluserpass")
    del_user_data = del_user_res.json()
    del_user_id = del_user_data['user']['id']
    del_user_token = del_user_data['X-API-TOKEN']
    create_testitem(
        client, del_user_id, del_user_token, 
        title="dummy_item", desc="dummy")

    # item移管先の確認用の3rd user
    create_testuser(
        client, email="3rd_user@", password="3rd")

    # ユーザー削除
    delete_res = client.post(
        f"/users/{del_user_id}/delete", 
        headers={'X-API-TOKEN': token})
    assert delete_res.status_code == 200
    deleted_user = delete_res.json()

    assert deleted_user['id'] == del_user_id
    assert deleted_user['is_active'] == False

    # 1stユーザーへのitem移管確認
    item_res = client.get(
        f"/me/items", headers={'X-API-TOKEN': token})
    items = item_res.json()
    titles = [iitem['title'] for iitem in items]
    assert user_id == 1
    assert len(items) == 2
    assert sorted(titles) == sorted(['dummy_item', 'item1'])

    # 削除ユーザーでのログイン不可
    fail_login_res = client.get(
        "/login/",
        params={"email": "deluser@", "password": "deluserpass"}
    )
    assert fail_login_res.status_code == 404

    # 削除ユーザーのトークン無効
    fail_token_res = client.get(
        f"/health-check", headers={'X-API-TOKEN': del_user_token})
    assert fail_token_res.status_code == 404

    # 削除ユーザーへのitem追加不可
    fail_itemcreate_res = create_testitem(client, del_user_id, token)
    assert fail_itemcreate_res.status_code == 404
