"""fastapi-babel統合のテスト"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_babel_integration():
    """Babel統合が正常に動作するか確認"""
    # デフォルト言語（日本語）でアクセス
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # 英語でアクセス
    response = client.get("/health", headers={"Accept-Language": "en"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    print("✓ Babel統合テスト成功")


if __name__ == "__main__":
    test_babel_integration()
