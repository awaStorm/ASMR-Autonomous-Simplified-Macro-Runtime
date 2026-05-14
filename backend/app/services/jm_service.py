"""禁漫服务"""
import os
import asyncio
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, asdict
from io import BytesIO

import jmcomic
import httpx
from PIL import Image


@dataclass
class JmHistoryItem:
    """历史记录项"""
    album_id: str
    title: str
    cover_path: Optional[str]
    created_at: float


class JmService:
    def __init__(self):
        project_root = Path(__file__).parent.parent.parent.parent
        
        self.base_dir = project_root / "data" / "jm"
        self.pdf_dir = self.base_dir / "pdf"
        self.stock_dir = self.base_dir / "stock"
        self.cover_dir = self.base_dir / "covers"
        self.history_file = self.base_dir / "history.json"
        
        # 确保目录存在
        for dir_path in [self.base_dir, self.pdf_dir, self.stock_dir, self.cover_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 硬编码配置，不依赖外部文件
        self.jm_option = self._create_jm_option()
        
        # 加载历史记录
        self.history: deque[JmHistoryItem] = deque(maxlen=10)
        self._load_history()
        
        # 下载任务状态
        self.download_tasks: Dict[str, Dict] = {}
    
    def _create_jm_option(self) -> jmcomic.JmOption:
        """创建 jmcomic 配置选项（直接仿照原插件）"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "jm_option.yml"
            
            if not config_path.exists():
                # 搜索配置文件
                for root, dirs, files in os.walk(Path(__file__).parent.parent.parent.parent):
                    for file in files:
                        if 'jm_option' in file.lower():
                            pass
            
            option = jmcomic.JmOption.from_file(str(config_path))
            return option
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
    
    def _load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        self.history.append(JmHistoryItem(**item))
            except Exception as e:
                pass
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(item) for item in self.history], f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass
    
    def _pdf_path(self, album_id: str) -> Path:
        """获取PDF路径"""
        return self.pdf_dir / f"{album_id}.pdf"
    
    def _cover_path(self, album_id: str) -> Path:
        """获取封面路径"""
        return self.cover_dir / f"{album_id}.jpg"
    
    async def start_download(self, album_id: str) -> Dict:
        """开始下载任务"""
        if album_id in self.download_tasks:
            return {
                "success": False,
                "error": "该本子正在下载中",
                "task_id": album_id
            }
        
        # 检查PDF是否已存在
        pdf_path = self._pdf_path(album_id)
        
        if pdf_path.exists():
            # 从历史记录中获取信息
            history_item = next((item for item in self.history if item.album_id == album_id), None)
            if not history_item:
                # 尝试从PDF文件名推断
                history_item = JmHistoryItem(
                    album_id=album_id,
                    title=f"本子 {album_id}",
                    cover_path=str(self._cover_path(album_id)) if self._cover_path(album_id).exists() else None,
                    created_at=pdf_path.stat().st_mtime
                )
                self.history.appendleft(history_item)
                self._save_history()
            
            return {
                "success": True,
                "cached": True,
                "album_id": album_id,
                "title": history_item.title
            }
        
        # 创建新任务
        self.download_tasks[album_id] = {
            "status": "downloading",
            "progress": 0,
            "title": "",
            "error": None
        }
        
        # 在后台运行下载
        asyncio.create_task(self._download_album(album_id))
        
        return {
            "success": True,
            "task_id": album_id,
            "status": "downloading"
        }
    
    async def _download_album(self, album_id: str):
        """异步下载本子"""
        try:
            # 先获取本子信息
            self.download_tasks[album_id]["status"] = "fetching_info"
            self.download_tasks[album_id]["progress"] = 10
            
            # 获取本子详情（优先用API）
            client = self.jm_option.new_jm_client()
            album_detail = await asyncio.to_thread(client.get_album_detail, album_id)
            
            if album_detail:
                # 获取标题（优先 title，其次 name）
                title = getattr(album_detail, 'title', None) or getattr(album_detail, 'name', f"本子 {album_id}")
                self.download_tasks[album_id]["title"] = title
                
                # 获取封面URL（尝试多种可能的字段名）
                cover_url = None
                for attr in ['cover', 'cover_url', 'cover_img', 'cover_image', 'img_url', 'image_url']:
                    cover_url = getattr(album_detail, attr, None)
                    if cover_url:
                        await self._download_cover_from_url(album_id, cover_url)
                        break
            
            # 下载本子
            self.download_tasks[album_id]["status"] = "downloading"
            self.download_tasks[album_id]["progress"] = 20
            
            # 在同步上下文中运行下载
            await asyncio.to_thread(
                lambda: self.jm_option.download_album([album_id])
            )
            
            self.download_tasks[album_id]["progress"] = 80
            
            # 等待PDF生成
            await asyncio.sleep(2)
            
            # 检查PDF
            pdf_path = self._pdf_path(album_id)
            if not pdf_path.exists():
                raise Exception(f"PDF文件未生成: {pdf_path}")
            
            # 提取封面
            self.download_tasks[album_id]["status"] = "extracting_cover"
            title = await self._extract_cover_and_title(album_id)
            
            # 保存到历史
            history_item = JmHistoryItem(
                album_id=album_id,
                title=title,
                cover_path=str(self._cover_path(album_id)) if self._cover_path(album_id).exists() else None,
                created_at=asyncio.get_event_loop().time()
            )
            self.history.appendleft(history_item)
            self._save_history()
            
            # 清理旧的PDF（只保留4个最近的）
            self._cleanup_old_pdfs()
            
            self.download_tasks[album_id]["status"] = "completed"
            self.download_tasks[album_id]["progress"] = 100
            self.download_tasks[album_id]["title"] = title
            
        except Exception as e:
            self.download_tasks[album_id]["status"] = "failed"
            self.download_tasks[album_id]["error"] = str(e)
    
    async def _download_cover_from_url(self, album_id: str, url: str):
        """从URL下载封面并压缩"""
        cover_path = self._cover_path(album_id)
        if cover_path.exists():
            return
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=30)
                resp.raise_for_status()
                
                img = Image.open(BytesIO(resp.content))
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # 压缩到合适大小
                img.thumbnail((300, 400), Image.Resampling.LANCZOS)
                img.save(cover_path, 'JPEG', quality=85)
                
        except Exception as e:
            pass
    
    async def _extract_cover_and_title(self, album_id: str) -> str:
        """提取封面和标题（降级逻辑）"""
        try:
            # 优先检查已保存的封面
            cover_path = self._cover_path(album_id)
            
            # 列出stock目录下的所有第一层子目录
            subdirs = [d for d in self.stock_dir.iterdir() if d.is_dir()]
            
            # 按修改时间排序，取最新的文件夹（因为下载完成后刚创建的就是当前本子）
            stock_album_dir = None
            if subdirs:
                # 按修改时间降序排序
                subdirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                stock_album_dir = subdirs[0]
            
            # 优先使用API获取的标题
            title = self.download_tasks.get(album_id, {}).get("title", f"本子 {album_id}")
            
            # 如果没有从API获取到，从目录名提取标题
            if title == f"本子 {album_id}" and stock_album_dir:
                title = stock_album_dir.name
            
            # 递归查找第一张图片作为封面
            if stock_album_dir:
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']:
                    image_files.extend(stock_album_dir.rglob(ext))
                
                # 排序确保顺序一致
                image_files = sorted(image_files)
                
                if image_files:
                    try:
                        cover_path = self._cover_path(album_id)
                        with Image.open(image_files[0]) as img:
                            # 保存为JPG
                            if img.mode in ('RGBA', 'P'):
                                img = img.convert('RGB')
                            img.save(cover_path, 'JPEG', quality=90)
                    except Exception as e:
                        pass
            
            return title
            
        except Exception as e:
            return f"本子 {album_id}（{album_id}）"
    
    def _cleanup_old_pdfs(self):
        """清理旧的PDF，只保留最近的4个"""
        if len(self.history) <= 4:
            return
        
        # 获取超过4个的旧记录
        old_items = list(self.history)[4:]
        
        for item in old_items:
            pdf_path = self._pdf_path(item.album_id)
            if pdf_path.exists():
                try:
                    pdf_path.unlink()
                except Exception as e:
                    pass
    
    def get_task_status(self, album_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.download_tasks.get(album_id)
    
    def get_history(self) -> List[Dict]:
        """获取历史记录（10个）"""
        return [asdict(item) for item in self.history]
    
    def get_recent(self) -> List[Dict]:
        """获取最近的4个本子"""
        recent_items = []
        for item in self.history:
            pdf_path = self._pdf_path(item.album_id)
            if pdf_path.exists():
                recent_items.append(asdict(item))
                if len(recent_items) >= 4:
                    break
        return recent_items
    
    def delete_item(self, album_id: str) -> bool:
        """删除本子及其相关数据"""
        try:
            # 从历史记录中移除
            new_history = deque(maxlen=10)
            for item in self.history:
                if item.album_id != album_id:
                    new_history.append(item)
            self.history = new_history
            self._save_history()
            
            # 删除PDF文件
            pdf_path = self._pdf_path(album_id)
            if pdf_path.exists():
                pdf_path.unlink()
            
            # 删除封面
            cover_path = self._cover_path(album_id)
            if cover_path.exists():
                cover_path.unlink()
            
            # 删除stock目录中的缓存文件夹
            # 查找匹配的文件夹（可能包含album_id）
            for subdir in self.stock_dir.iterdir():
                if subdir.is_dir() and album_id in subdir.name:
                    shutil.rmtree(subdir, ignore_errors=True)
            
            return True
        except Exception as e:
            print(f"删除本子失败: {e}")
            return False


# 单例
jm_service = JmService()
