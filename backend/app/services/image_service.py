"""图片搜索服务"""
import hashlib
import json
import os
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple

import aiohttp

from ..config import image_config, settings

# 预设的 API URL（写死在代码中）
PRESET_API_URLS = {
    'baidu': 'https://cn.apihz.cn/api/img/apihzimgbaidu.php',
    'pexels': 'https://api.pexels.com/v1/search',
    'cat': 'https://api.thecatapi.com/v1/images/search',
    'lolicon': 'https://api.lolicon.app/setu/v2'
}

# API 配置要求
API_REQUIREMENTS = {
    'baidu': {'needs_key': True, 'needs_user_id': True, 'needs_url': False},
    'pexels': {'needs_key': True, 'needs_user_id': False, 'needs_url': False},
    'cat': {'needs_key': False, 'needs_user_id': False, 'needs_url': False},
    'lolicon': {'needs_key': False, 'needs_user_id': False, 'needs_url': False}
}

# API 配置文件路径
API_CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "api_keys.json"


def _load_api_keys_from_file() -> dict:
    """从文件加载 API 密钥"""
    if API_CONFIG_FILE.exists():
        try:
            with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_api_keys_to_file(keys: dict):
    """保存 API 密钥到文件"""
    try:
        API_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存 API 配置失败: {e}")


def get_image_config() -> dict:
    """获取图片搜索配置"""
    return image_config.get('image_search', {})


def get_source_config(source: str) -> dict:
    """获取指定来源的配置，预设 URL，密钥从环境变量或配置文件获取"""
    config = get_image_config().get(source, {})

    # 设置预设的 API URL
    config['api_url'] = PRESET_API_URLS.get(source, '')

    # 从环境变量获取 API 密钥（优先级最高）
    # 然后从配置文件获取
    file_keys = _load_api_keys_from_file()

    if source == 'baidu':
        config['api_key'] = os.getenv('BAIDU_API_KEY', file_keys.get('baidu', {}).get('api_key', ''))
        config['user_id'] = os.getenv('BAIDU_USER_ID', file_keys.get('baidu', {}).get('user_id', ''))
    elif source == 'pexels':
        config['api_key'] = os.getenv('PEXELS_API_KEY', file_keys.get('pexels', {}).get('api_key', ''))
    elif source == 'cat':
        config['api_key'] = os.getenv('CAT_API_KEY', file_keys.get('cat', {}).get('api_key', ''))
    # Lolicon 不需要 API Key

    return config


def get_saved_api_keys() -> dict:
    """获取已保存的 API 密钥（用于前端显示）"""
    return _load_api_keys_from_file()


def set_api_key(source: str, api_key: str = "", user_id: str = "") -> bool:
    """设置 API 密钥"""
    try:
        keys = _load_api_keys_from_file()

        if source not in keys:
            keys[source] = {}

        if api_key:
            keys[source]['api_key'] = api_key
        if user_id:
            keys[source]['user_id'] = user_id

        _save_api_keys_to_file(keys)
        return True
    except Exception:
        return False


def check_api_config(source: str) -> Dict[str, str]:
    """检查 API 配置是否完整，返回错误信息"""
    config = get_source_config(source)
    requirements = API_REQUIREMENTS.get(source, {})
    errors = []

    # 检查 URL（虽然预设了，但还是检查一下）
    if requirements.get('needs_url', False) and not config.get('api_url'):
        errors.append('API URL 未配置')
    elif not config.get('api_url'):
        errors.append('API URL 未配置')

    # 检查密钥
    if requirements.get('needs_key', False) and not config.get('api_key'):
        errors.append('API Key 未配置')

    # 检查用户ID
    if requirements.get('needs_user_id', False) and not config.get('user_id'):
        errors.append('User ID 未配置')

    return errors


class DeduplicationManager:
    """去重管理器（基于文件存储，自动过期）"""

    def __init__(self, data_dir: Path, expire_days: int = 7):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "search_history.json"
        self.expire_seconds = expire_days * 24 * 3600
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def _clean_expired(self):
        current_time = time.time()
        expired_count = 0

        for keyword in list(self.history.keys()):
            for url_hash in list(self.history[keyword].keys()):
                timestamp = self.history[keyword][url_hash]
                if current_time - timestamp > self.expire_seconds:
                    del self.history[keyword][url_hash]
                    expired_count += 1

            if not self.history[keyword]:
                del self.history[keyword]

        if expired_count > 0:
            print(f"清理了 {expired_count} 条过期记录")
            self._save_history()

    def get_image_hash(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def filter_duplicates(self, keyword: str, urls: List[str]) -> List[str]:
        self._clean_expired()

        keyword_lower = keyword.lower()
        current_time = time.time()

        if keyword_lower not in self.history:
            self.history[keyword_lower] = {}

        unique_urls = []
        for url in urls:
            url_hash = self.get_image_hash(url)
            if url_hash not in self.history[keyword_lower]:
                unique_urls.append(url)
                self.history[keyword_lower][url_hash] = current_time

        if unique_urls:
            self._save_history()

        return unique_urls

    def get_stats(self) -> Dict:
        self._clean_expired()
        total_images = sum(len(images) for images in self.history.values())
        return {
            "total_keywords": len(self.history),
            "total_images": total_images,
            "expire_days": self.expire_seconds // 86400
        }


class ImageAPI:
    """图片搜索API封装"""

    @staticmethod
    def _add_cache_buster(url: str) -> str:
        """添加缓存破坏参数，防止返回相同缓存"""
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}_cb={random.randint(100000, 999999)}"

    @staticmethod
    async def search_baidu(keyword: str, count: int = 3) -> Tuple[bool, List[str]]:
        """百度图片搜索"""
        config = get_source_config('baidu')
        api_url = config.get('api_url')
        user_id = config.get('user_id')
        api_key = config.get('api_key')

        if not all([api_url, user_id, api_key]):
            return False, []

        params = {
            "id": user_id,
            "key": api_key,
            "words": keyword,
            "page": random.randint(1, 5),
            "limit": count,
            "type": 1
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == 200:
                            urls = data.get('res', [])
                            urls = [ImageAPI._add_cache_buster(url) for url in urls]
                            return True, urls
                    return False, []
        except Exception:
            return False, []

    @staticmethod
    async def search_pexels(keyword: str, count: int = 3) -> Tuple[bool, List[str]]:
        """Pexels API搜索"""
        config = get_source_config('pexels')
        api_url = config.get('api_url')
        api_key = config.get('api_key')

        if not all([api_url, api_key]):
            return False, []

        headers = {"Authorization": api_key}
        params = {
            "query": keyword,
            "per_page": count,
            "page": random.randint(1, 10)
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        photos = data.get('photos', [])
                        urls = [p.get('src', {}).get('original') for p in photos if p.get('src')]
                        urls = [url for url in urls if url]
                        return True, urls
                    return False, []
        except Exception:
            return False, []

    @staticmethod
    async def get_random_cat(count: int = 1) -> Tuple[bool, List[str]]:
        """获取随机猫图（公共API，无需密钥）"""
        config = get_source_config('cat')
        api_url = config.get('api_url')
        api_key = config.get('api_key')

        if not api_url:
            return False, []

        params = {
            "limit": min(count, 100)
        }

        # 只有当有 API Key 时才添加（无密钥时使用演示模式）
        if api_key:
            params["api_key"] = api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        urls = [item.get('url') for item in data if item.get('url')]
                        return True, urls
                    return False, []
        except Exception:
            return False, []

    @staticmethod
    async def search_lolicon(keyword: str = "", count: int = 3, r18: int = 0) -> Tuple[bool, List[str]]:
        """Lolicon API搜索"""
        config = get_source_config('lolicon')
        api_url = config.get('api_url')

        if not api_url:
            return False, []

        params = {
            "r18": r18,
            "num": min(count, 10)
        }

        if keyword:
            params["tag[]"] = keyword

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # 检查 API 返回的 error 字段
                        if data.get('error') != "":
                            return False, []
                        # 正确解析 urls.original
                        urls = [item.get('urls', {}).get('original')
                                for item in data.get('data', [])
                                if item.get('urls', {}).get('original')]
                        return True, urls
                    return False, []
        except Exception:
            return False, []


class ImageService:
    """图片搜索服务"""

    def __init__(self):
        self.data_dir = Path(settings.data_dir)
        self.deduplication = DeduplicationManager(self.data_dir / "image_search")

    async def search_images(self, keyword: str, count: int, source: str = "baidu", r18: int = 0) -> List[str]:
        """搜索图片"""
        if source == "baidu":
            success, urls = await ImageAPI.search_baidu(keyword, count)
        elif source == "pexels":
            success, urls = await ImageAPI.search_pexels(keyword, count)
        elif source == "cat":
            success, urls = await ImageAPI.get_random_cat(count)
        elif source == "lolicon":
            success, urls = await ImageAPI.search_lolicon(keyword, count, r18)
        else:
            success, urls = await ImageAPI.search_baidu(keyword, count)

        if success and urls:
            urls = self.deduplication.filter_duplicates(keyword, urls)
            return urls[:count]
        return []

    async def get_cat_images(self, count: int = 3) -> List[str]:
        """获取随机猫图"""
        success, urls = await ImageAPI.get_random_cat(count)
        if success and urls:
            urls = self.deduplication.filter_duplicates("cat", urls)
            return urls[:count]
        return []

    async def get_lolicon_images(self, keyword: str = "", count: int = 3, r18: int = 0) -> List[str]:
        """获取Lolicon图片"""
        success, urls = await ImageAPI.search_lolicon(keyword, count, r18)
        if success and urls:
            urls = self.deduplication.filter_duplicates(keyword, urls)
            return urls[:count]
        return []

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.deduplication.get_stats()
