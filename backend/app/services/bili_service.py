"""B站监控服务"""
import asyncio
import hashlib
import json
import random
import time
import re
import os
import tempfile
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Set, Deque
from dataclasses import dataclass, field
from collections import deque

import requests
import httpx
import qrcode

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import settings

MIN_SEND_INTERVAL = 10
MAX_SEND_INTERVAL = 20

# 定时任务调度器
scheduler = None


@dataclass
class UPConfig:
    uid: str
    name: str
    target_groups: List[str] = field(default_factory=list)
    check_interval: int = 3600
    enabled: bool = True
    last_check: float = 0

    @property
    def sent_file(self) -> str:
        return f"{self.uid}_sent.json"

    @property
    def cache_file(self) -> str:
        return f"{self.uid}_cache.json"


@dataclass
class PluginState:
    cookies: Optional[Dict] = None
    is_running: bool = False
    monitor_task = None
    sent_images: Dict[str, Set[str]] = field(default_factory=dict)
    cached_images: Dict[str, Deque[Dict]] = field(default_factory=dict)
    sent_stats: Dict[str, int] = field(default_factory=dict)


class BiliFileManager:
    """文件管理器"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_cookies(self) -> Optional[Dict]:
        cookie_file = self.data_dir / "bili_cookies.json"
        if not cookie_file.exists():
            return None

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            saved_time = cookies.get('_saved_at', 0)
            if time.time() - saved_time < 7 * 24 * 3600:
                return {k: str(v) for k, v in cookies.items() if not k.startswith('_')}
        except Exception as e:
            print(f"加载Cookie失败: {e}")
        return None

    def save_cookies(self, cookies: Dict) -> bool:
        cookie_file = self.data_dir / "bili_cookies.json"
        try:
            cookies_with_meta = {k: v for k, v in cookies.items()}
            cookies_with_meta['_saved_at'] = int(time.time())
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies_with_meta, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存Cookie失败: {e}")
            return False

    def load_config(self) -> Dict:
        """加载配置文件"""
        config_file = self.data_dir / "config.json"
        if not config_file.exists():
            return {}
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}

    def save_config(self, config: Dict) -> bool:
        """保存配置文件"""
        config_file = self.data_dir / "config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def load_sent_images(self, filename: str) -> Set[str]:
        file_path = self.data_dir / filename
        if not file_path.exists():
            return set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()

    def save_sent_images(self, filename: str, sent_set: Set[str]):
        file_path = self.data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(list(sent_set), f, ensure_ascii=False, indent=2)

    def load_cached_images(self, filename: str) -> Deque[Dict]:
        file_path = self.data_dir / filename
        if not file_path.exists():
            return deque(maxlen=10)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return deque(data, maxlen=10)
        except:
            return deque(maxlen=10)

    def save_cached_images(self, filename: str, cache: Deque[Dict]):
        file_path = self.data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(list(cache), f, ensure_ascii=False, indent=2)

    def load_stats(self) -> Dict[str, int]:
        """加载已发统计数据"""
        stats_file = self.data_dir / "sent_stats.json"
        if not stats_file.exists():
            return {}
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载统计数据失败: {e}")
            return {}

    def save_stats(self, stats: Dict[str, int]) -> bool:
        """保存已发统计数据（原子写入）"""
        stats_file = self.data_dir / "sent_stats.json"
        try:
            fd, temp_path = tempfile.mkstemp(
                suffix='.json',
                prefix='sent_stats_',
                dir=str(self.data_dir)
            )
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
                os.replace(temp_path, str(stats_file))
                return True
            except Exception as e:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e
        except Exception as e:
            print(f"保存统计数据失败: {e}")
            return False

    def update_stats_atomic(self, up_name: str, increment: int) -> bool:
        """原子更新单个UP主的已发统计"""
        stats = self.load_stats()
        stats[up_name] = stats.get(up_name, 0) + increment
        return self.save_stats(stats)


def generate_image_hash(url: str, dynamic_id: str) -> str:
    content = f"{url}_{dynamic_id}"
    return hashlib.md5(content.encode()).hexdigest()


class BiliAPI:
    """B站API封装"""

    @staticmethod
    def get_login_qr() -> Tuple[Optional[str], Optional[Dict]]:
        """获取登录二维码和二维码密钥（保留旧接口兼容）"""
        try:
            resp = requests.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            data = resp.json()

            if data.get("code") != 0:
                return None, {"error": f"获取二维码失败: {data.get('message')}"}

            qrcode_key = data["data"]["qrcode_key"]
            qr_url = data["data"]["url"]

            return qrcode_key, {"qr_url": qr_url, "qrcode_key": qrcode_key}
        except Exception as e:
            print(f"获取二维码失败: {e}")
            return None, {"error": f"获取二维码失败: {e}"}

    @staticmethod
    def get_login_qr_image() -> Tuple[Optional[str], Optional[str], Optional[bytes]]:
        """获取登录二维码（使用 qrcode 库本地生成）"""
        try:
            # 第一步：从B站获取短链接
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
                timeout=10,
                headers=headers
            )
            data = resp.json()

            if data.get("code") != 0:
                print(f"获取二维码信息失败: {data}")
                return None, None, None

            qrcode_key = data["data"]["qrcode_key"]
            qr_url = data["data"]["url"]
            
            # 第二步：用 qrcode 库把短链接生成本地二维码图片
            qr = qrcode.QRCode(box_size=8, border=4)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转为 bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            image_data = buffer.getvalue()

            return qrcode_key, "image/png", image_data
        except Exception as e:
            print(f"获取二维码失败: {e}")
            return None, None, None

    @staticmethod
    def poll_login(qrcode_key: str) -> Tuple[Optional[Dict], Optional[str]]:
        """轮询登录状态（同步版本，保留兼容性）"""
        for _ in range(60):
            try:
                resp = requests.get(
                    "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                    params={"qrcode_key": qrcode_key},
                    timeout=10,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                data = resp.json()

                if data.get("code") == 0 and "data" in data:
                    data_code = data["data"].get("code")

                    if data_code == 0:
                        cookies = BiliAPI._parse_cookie(resp.headers.get('Set-Cookie', ''))
                        if cookies:
                            return cookies, None
                        return None, "未获取到Cookie"
                    elif data_code == 86090:
                        return None, "scanned"
                    elif data_code == 86038:
                        return None, "expired"
            except Exception as e:
                print(f"轮询异常: {e}")

            time.sleep(2)

        return None, "登录超时"

    @staticmethod
    async def poll_login_async(qrcode_key: str) -> Tuple[Optional[Dict], Optional[str]]:
        """轮询登录状态（异步版本，不阻塞事件循环）"""
        for _ in range(60):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                        params={"qrcode_key": qrcode_key},
                        timeout=10.0,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    data = resp.json()

                    if data.get("code") == 0 and "data" in data:
                        data_code = data["data"].get("code")

                        if data_code == 0:
                            cookies = BiliAPI._parse_cookie(resp.headers.get('Set-Cookie', ''))
                            if cookies:
                                return cookies, None
                            return None, "未获取到Cookie"
                        elif data_code == 86090:
                            return None, "scanned"
                        elif data_code == 86038:
                            return None, "expired"
            except Exception as e:
                print(f"轮询异常: {e}")

            await asyncio.sleep(2)

        return None, "登录超时"

    @staticmethod
    def _parse_cookie(set_cookie: str) -> Dict:
        cookies = {}
        patterns = [
            (r'SESSDATA=([^;,\s]+)', 'SESSDATA'),
            (r'bili_jct=([^;,\s]+)', 'bili_jct'),
            (r'DedeUserID=([^;,\s]+)', 'DedeUserID'),
            (r'DedeUserID__ckMd5=([^;,\s]+)', 'DedeUserID__ckMd5'),
            (r'sid=([^;,\s]+)', 'sid'),
        ]
        for pattern, key in patterns:
            match = re.search(pattern, set_cookie)
            if match:
                cookies[key] = str(match.group(1))
        return cookies

    @staticmethod
    async def fetch_dynamics_async(cookies: Dict, up_uid: str) -> List:
        url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={up_uid}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://space.bilibili.com/{up_uid}"
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    timeout=15.0,
                    verify=False
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        return data["data"].get("items", [])
                elif resp.status_code == 403:
                    print(f"获取动态失败: 403权限不足，可能是Cookie已过期或请求过于频繁")
        except Exception as e:
            print(f"获取动态失败: {e}")
        return []

    @staticmethod
    def fetch_dynamics(cookies: Dict, up_uid: str) -> List:
        url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={up_uid}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://space.bilibili.com/{up_uid}"
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=15,
                verify=False
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    return data["data"].get("items", [])
            elif resp.status_code == 403:
                print(f"获取动态失败: 403权限不足，可能是Cookie已过期或请求过于频繁")
        except Exception as e:
            print(f"获取动态失败: {e}")
        return []

    @staticmethod
    def extract_images(dynamic: Dict) -> List[Dict]:
        images = []
        try:
            if dynamic.get("type") != "DYNAMIC_TYPE_DRAW":
                return images

            modules = dynamic.get("modules", {})
            module_author = modules.get("module_author", {})
            module_dynamic = modules.get("module_dynamic", {})

            desc = module_dynamic.get("desc", {})
            description = desc.get("text", "") if desc else ""

            topic = module_dynamic.get("topic", {})
            topic_name = topic.get("name", "") if topic else ""
            if topic_name and not description:
                description = f"#{topic_name}#"

            major = module_dynamic.get("major", {})
            if major.get("type") != "MAJOR_TYPE_DRAW":
                return images

            draw = major.get("draw", {})
            for pic in draw.get("items", []):
                img_url = pic.get("src", "")
                if not img_url:
                    continue
                if img_url.startswith("http://"):
                    img_url = img_url.replace("http://", "https://", 1)

                images.append({
                    "url": img_url,
                    "description": description,
                    "pub_text": module_author.get("pub_time", ""),
                    "dynamic_id": str(dynamic.get("id_str", "")),
                })
        except Exception as e:
            print(f"提取图片异常: {e}")
        return images


class BiliMonitorService:
    """B站监控服务"""

    def __init__(self):
        data_dir = settings.data_dir / "bili"
        self.file_mgr = BiliFileManager(data_dir)
        self.state = PluginState()
        self.up_configs: Dict[str, UPConfig] = {}
        self.state.cookies = self.file_mgr.load_cookies()
        
        # 加载配置并初始化UP主列表
        self._load_config_and_ups()

    def _migrate_old_config(self, saved_config: Dict) -> Dict:
        """迁移旧配置格式到新格式"""
        # 如果已经是新格式，直接返回
        if 'ups' in saved_config and saved_config['ups']:
            return saved_config
        
        # 旧格式迁移：从 up_intervals 和硬编码默认值构建新格式
        migrated_config = {
            'check_on_start': saved_config.get('check_on_start', False),
            'ups': []
        }
        
        up_intervals = saved_config.get('up_intervals', {})
        
        # 旧版默认UP主（用于迁移）
        legacy_defaults = {
            "夏莱烤肉屋": "3546575051688471",
            "狐狐月nya": "415470107"
        }
        
        for name, uid in legacy_defaults.items():
            interval = up_intervals.get(name, 60)
            migrated_config['ups'].append({
                "name": name,
                "uid": uid,
                "check_interval": interval,
                "enabled": True
            })
        
        # 添加 up_intervals 中其他未知的UP主（但没有uid信息，无法恢复）
        for name, interval in up_intervals.items():
            if name not in legacy_defaults:
                migrated_config['ups'].append({
                    "name": name,
                    "uid": "",
                    "check_interval": interval,
                    "enabled": True
                })
        
        return migrated_config

    def _load_config_and_ups(self):
        """加载配置文件并初始化UP主列表（单一配置源）"""
        saved_config = self.file_mgr.load_config()
        
        # 配置迁移
        if 'up_intervals' in saved_config and 'ups' not in saved_config:
            saved_config = self._migrate_old_config(saved_config)
            self.file_mgr.save_config(saved_config)
        
        self.check_on_start = saved_config.get('check_on_start', False)
        self.state.sent_stats = self.file_mgr.load_stats()
        
        # 从配置文件加载UP主列表
        ups = saved_config.get('ups', [])
        
        for up in ups:
            # 跳过uid为空的无效条目（迁移时可能产生）
            if not up.get('uid'):
                continue
                
            config = UPConfig(
                uid=up["uid"],
                name=up["name"],
                check_interval=up.get("check_interval", 60) * 60,
                enabled=up.get("enabled", True)
            )
            self.up_configs[up["name"]] = config
            self.state.sent_images[up["name"]] = self.file_mgr.load_sent_images(config.sent_file)
            self.state.cached_images[up["name"]] = self.file_mgr.load_cached_images(config.cache_file)

            if up["name"] not in self.state.sent_stats:
                cache_count = len(self.state.cached_images[up["name"]])
                self.state.sent_stats[up["name"]] = cache_count
        
        self.file_mgr.save_stats(self.state.sent_stats)

    def save_config(self, check_on_start: bool = None):
        """保存配置（单一配置源）"""
        if check_on_start is not None:
            self.check_on_start = check_on_start
        
        config = {
            'check_on_start': self.check_on_start,
            'ups': [
                {
                    "name": name,
                    "uid": config.uid,
                    "check_interval": config.check_interval // 60,
                    "enabled": config.enabled
                }
                for name, config in self.up_configs.items()
            ]
        }
        return self.file_mgr.save_config(config)

    def get_config(self) -> Dict:
        """获取当前配置"""
        return {
            'check_on_start': self.check_on_start,
            'ups': [
                {
                    "name": name,
                    "uid": config.uid,
                    "check_interval": config.check_interval // 60,
                    "enabled": config.enabled
                }
                for name, config in self.up_configs.items()
            ]
        }

    def get_login_qr(self) -> Tuple[Optional[str], Optional[Dict]]:
        return BiliAPI.get_login_qr()

    def get_login_qr_image(self) -> Tuple[Optional[str], Optional[str], Optional[bytes]]:
        return BiliAPI.get_login_qr_image()

    def wait_login(self, qrcode_key: str) -> Tuple[bool, str]:
        """等待登录（同步版本，保留兼容性）"""
        cookies, error = BiliAPI.poll_login(qrcode_key)
        if cookies:
            self.state.cookies = cookies
            self.file_mgr.save_cookies(cookies)
            return True, "登录成功"
        if error == "scanned":
            return False, "scanned"
        if error == "expired":
            return False, "二维码已过期"
        return False, error or "登录失败"

    async def wait_login_async(self, qrcode_key: str) -> Tuple[bool, str]:
        """等待登录（异步版本，不阻塞事件循环）"""
        cookies, error = await BiliAPI.poll_login_async(qrcode_key)
        if cookies:
            self.state.cookies = cookies
            self.file_mgr.save_cookies(cookies)
            return True, "登录成功"
        if error == "scanned":
            return False, "scanned"
        if error == "expired":
            return False, "二维码已过期"
        return False, error or "登录失败"

    def check_up(self, up_name: str, delay: Tuple[float, float] = (2, 4)) -> List[Dict]:
        if up_name not in self.up_configs:
            return []

        config = self.up_configs[up_name]
        if not self.state.cookies:
            return []

        delay_seconds = random.uniform(delay[0], delay[1])
        time.sleep(delay_seconds)

        dynamics = BiliAPI.fetch_dynamics(self.state.cookies, config.uid)
        if not dynamics:
            return []

        new_images = []
        for dynamic in dynamics[:10]:
            images = BiliAPI.extract_images(dynamic)
            for img in images:
                img_hash = generate_image_hash(img['url'], img['dynamic_id'])

                if img_hash not in self.state.sent_images[up_name]:
                    self.state.sent_images[up_name].add(img_hash)
                    new_images.append(img)

                    cache = self.state.cached_images[up_name]
                    cache.appendleft(img)
                    if len(cache) > 10:
                        cache.pop()

        if new_images:
            self.file_mgr.save_sent_images(config.sent_file, self.state.sent_images[up_name])
            self.file_mgr.save_cached_images(config.cache_file, self.state.cached_images[up_name])
            
            self.state.sent_stats[up_name] = self.state.sent_stats.get(up_name, 0) + len(new_images)
            self.file_mgr.update_stats_atomic(up_name, len(new_images))

        # 反转顺序，确保最新的图片排在最前面
        return new_images[::-1]

    async def check_up_async(self, up_name: str, delay: Tuple[float, float] = (0.5, 1.5)) -> List[Dict]:
        if up_name not in self.up_configs:
            return []

        config = self.up_configs[up_name]
        if not self.state.cookies:
            return []

        await asyncio.sleep(random.uniform(delay[0], delay[1]))

        dynamics = await BiliAPI.fetch_dynamics_async(self.state.cookies, config.uid)
        if not dynamics:
            return []

        new_images = []
        for dynamic in dynamics[:10]:
            images = BiliAPI.extract_images(dynamic)
            for img in images:
                img_hash = generate_image_hash(img['url'], img['dynamic_id'])

                if img_hash not in self.state.sent_images[up_name]:
                    self.state.sent_images[up_name].add(img_hash)
                    new_images.append(img)

                    cache = self.state.cached_images[up_name]
                    cache.appendleft(img)
                    if len(cache) > 10:
                        cache.pop()

        if new_images:
            self.file_mgr.save_sent_images(config.sent_file, self.state.sent_images[up_name])
            self.file_mgr.save_cached_images(config.cache_file, self.state.cached_images[up_name])
            
            self.state.sent_stats[up_name] = self.state.sent_stats.get(up_name, 0) + len(new_images)
            await asyncio.to_thread(self.file_mgr.update_stats_atomic, up_name, len(new_images))

        # 反转顺序，确保最新的图片排在最前面
        return new_images[::-1]

    def check_all(self, delay: Tuple[float, float] = (3, 5)) -> Dict[str, List[Dict]]:
        results = {}
        for up_name in self.up_configs:
            if not self.up_configs[up_name].enabled:
                continue
            images = self.check_up(up_name, delay)
            if images:
                results[up_name] = images
        return results

    async def check_all_async(self) -> Dict[str, List[Dict]]:
        results = {}
        tasks = []
        up_names = []
        
        for up_name in self.up_configs:
            if not self.up_configs[up_name].enabled:
                continue
            tasks.append(self.check_up_async(up_name))
            up_names.append(up_name)
        
        if not tasks:
            return results
        
        task_results = await asyncio.gather(*tasks)
        
        for up_name, images in zip(up_names, task_results):
            if images:
                results[up_name] = images
        
        return results

    def get_cached_images(self, up_name: str) -> List[Dict]:
        if up_name not in self.state.cached_images:
            return []
        return list(self.state.cached_images[up_name])

    def get_status(self) -> Dict:
        up_list = []
        for name, config in self.up_configs.items():
            sent_count = self.state.sent_stats.get(name, 0)
            cache_count = len(self.state.cached_images.get(name, []))
            up_list.append({
                "name": name,
                "uid": config.uid,
                "enabled": config.enabled,
                "sent_count": sent_count,
                "cache_count": cache_count,
                "check_interval": config.check_interval // 60
            })

        return {
            "logged_in": self.state.cookies is not None,
            "is_running": self.state.is_running,
            "up_count": len(self.up_configs),
            "ups": up_list
        }

    def get_ups(self) -> List[Dict]:
        return [
            {
                "name": name,
                "uid": config.uid,
                "enabled": config.enabled,
                "check_interval": config.check_interval // 60,
                "sent_count": self.state.sent_stats.get(name, 0),
                "cache_count": len(self.state.cached_images.get(name, []))
            }
            for name, config in self.up_configs.items()
        ]

    def start_scheduler(self, check_on_start: bool = False):
        """启动定时任务调度器"""
        global scheduler
        if scheduler is not None:
            scheduler.shutdown()
        
        scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
        
        # 为每个UP主添加定时任务
        for up_name, config in self.up_configs.items():
            if config.enabled and config.check_interval > 0:
                scheduler.add_job(
                    self._scheduled_check_up,
                    trigger=IntervalTrigger(minutes=config.check_interval // 60),
                    args=[up_name],
                    id=f"bili_check_{up_name}",
                    replace_existing=True
                )
        
        # 启动时是否主动检查一次
        if check_on_start and self.state.cookies:
            asyncio.create_task(self._check_all_on_start())
        
        scheduler.start()
        self.state.is_running = True

    def stop_scheduler(self):
        """停止定时任务调度器"""
        global scheduler
        if scheduler is not None:
            scheduler.shutdown()
            scheduler = None
        self.state.is_running = False

    def update_up_interval(self, up_name: str, interval_minutes: int):
        """更新UP主检查间隔"""
        if up_name in self.up_configs:
            self.up_configs[up_name].check_interval = interval_minutes * 60
            # 如果调度器正在运行，更新任务
            global scheduler
            if scheduler is not None and self.up_configs[up_name].enabled:
                scheduler.reschedule_job(
                    f"bili_check_{up_name}",
                    trigger=IntervalTrigger(minutes=interval_minutes)
                )

    def _scheduled_check_up(self, up_name: str):
        """定时检查单个UP主（调度器调用）"""
        if not self.state.cookies:
            return
        self.check_up(up_name, delay=(0, 1))

    async def _check_all_on_start(self):
        """启动时检查所有UP主"""
        for up_name, config in self.up_configs.items():
            if config.enabled:
                self.check_up(up_name, delay=(1, 2))
                await asyncio.sleep(2)  # 间隔2秒避免请求过快

    def add_up(self, name: str, uid: str, check_interval: int = 60, enabled: bool = True) -> bool:
        """添加新的UP主监控"""
        if name in self.up_configs:
            return False
        
        config = UPConfig(
            uid=uid,
            name=name,
            check_interval=check_interval * 60,
            enabled=enabled
        )
        self.up_configs[name] = config
        self.state.sent_images[name] = self.file_mgr.load_sent_images(config.sent_file)
        self.state.cached_images[name] = self.file_mgr.load_cached_images(config.cache_file)

        cache_count = len(self.state.cached_images[name])
        self.state.sent_stats[name] = cache_count
        self.file_mgr.save_stats(self.state.sent_stats)

        self.save_config()
        
        global scheduler
        if scheduler is not None and enabled:
            scheduler.add_job(
                self._scheduled_check_up,
                trigger=IntervalTrigger(minutes=check_interval),
                args=[name],
                id=f"bili_check_{name}",
                replace_existing=True
            )
        
        return True

    def remove_up(self, name: str) -> bool:
        """移除UP主监控"""
        if name not in self.up_configs:
            return False
        
        global scheduler
        if scheduler is not None:
            scheduler.remove_job(f"bili_check_{name}")
        
        del self.up_configs[name]
        del self.state.sent_images[name]
        del self.state.cached_images[name]
        
        if name in self.state.sent_stats:
            del self.state.sent_stats[name]
            self.file_mgr.save_stats(self.state.sent_stats)
        
        self.save_config()
        
        return True

    def toggle_up_enabled(self, name: str) -> bool:
        """切换UP主启用状态"""
        if name not in self.up_configs:
            return False
        
        self.up_configs[name].enabled = not self.up_configs[name].enabled
        enabled = self.up_configs[name].enabled
        
        global scheduler
        if scheduler is not None:
            job_id = f"bili_check_{name}"
            if enabled:
                scheduler.add_job(
                    self._scheduled_check_up,
                    trigger=IntervalTrigger(minutes=self.up_configs[name].check_interval // 60),
                    args=[name],
                    id=job_id,
                    replace_existing=True
                )
            else:
                scheduler.remove_job(job_id)
        
        self.save_config()
        
        return True


bili_service = BiliMonitorService()
