from pydantic_settings import BaseSettings
from pathlib import Path
import yaml
import os


class Settings(BaseSettings):
    """应用配置管理"""

    app_name: str = "ASMR API"
    debug: bool = True
    database_url: str = "sqlite:///./data/todos.db"
    data_dir: Path = Path(__file__).parent.parent / "data"
    static_dir: Path = Path(__file__).parent.parent / "static"
    backend_cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    port: int = 8137

    # 图片搜索 API 密钥（从环境变量获取）
    baidu_api_key: str = ""
    baidu_user_id: str = ""
    pexels_api_key: str = ""
    cat_api_key: str = ""

    class Config:
        env_file = ".env"


def load_image_config() -> dict:
    """从 config.yaml 加载图片搜索配置，支持环境变量替换"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 替换环境变量 ${VAR:-default}
            content = os.path.expandvars(content)
            return yaml.safe_load(content)
    return {}


settings = Settings()
image_config = load_image_config()
