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


def get_image_config() -> dict:
    """获取图片搜索配置"""
    return image_config.get('image_search', {})


def get_source_config(source: str) -> dict:
    """获取指定来源的配置，优先从环境变量读取敏感信息"""
    config = get_image_config().get(source, {})
    
    # 优先从环境变量获取 API 密钥
    if source == 'baidu':
        config['api_key'] = os.getenv('BAIDU_API_KEY', config.get('api_key', ''))
        config['user_id'] = os.getenv('BAIDU_USER_ID', config.get('user_id', ''))
        config['api_url'] = os.getenv('BAIDU_API_URL', config.get('api_url', ''))
    elif source == 'pexels':
        config['api_key'] = os.getenv('PEXELS_API_KEY', config.get('api_key', ''))
        config['api_url'] = os.getenv('PEXELS_API_URL', config.get('api_url', ''))
    elif source == 'cat':
        config['api_key'] = os.getenv('CAT_API_KEY', config.get('api_key', ''))
        config['api_url'] = os.getenv('CAT_API_URL', config.get('api_url', ''))
    elif source == 'lolicon':
        config['api_url'] = os.getenv('LOLICON_API_URL', config.get('api_url', ''))
    
    return config


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
        """获取随机猫图"""
        config = get_source_config('cat')
        api_url = config.get('api_url')
        api_key = config.get('api_key')

        if not all([api_url, api_key]):
            return False, []

        params = {
            "limit": min(count, 100),
            "api_key": api_key
        }

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
            "keyword": keyword,
            "num": min(count, 10),
            "r18": r18
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        urls = [item.get('url') for item in data.get('data', []) if item.get('url')]
                        return True, urls
                    return False, []
        except Exception:
            return False, []
