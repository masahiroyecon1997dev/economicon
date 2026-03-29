# root/api/gen_openapi.py
import json
import os

from fastapi.openapi.utils import get_openapi

from main import app  # FastAPIインスタンスがあるファイル


def generate_spec():
    openapi_schema = get_openapi(
        title="Economicon App API",
        version="0.2.0",
        routes=app.routes,
    )

    # 出力先を root/openapi.json に設定（一つ上の階層）
    output_path = os.path.join(
        os.path.dirname(__file__), "../app", "openapi.json"
    )

    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Successfully generated openapi.json at {output_path}")


if __name__ == "__main__":
    generate_spec()
