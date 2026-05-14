"""B站监控API"""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict
import requests
import asyncio

from ..services.bili_service import bili_service

router = APIRouter()

BILI_REFERER = "https://www.bilibili.com/"

login_tasks: Dict[str, asyncio.Task] = {}
login_results: Dict[str, dict] = {}


class LoginResponse(BaseModel):
    qrcode_key: str
    qr_url: str


class LoginResult(BaseModel):
    success: bool
    message: str


class PollLoginRequest(BaseModel):
    qrcode_key: str


class CheckResult(BaseModel):
    success: bool
    images: List[Dict]
    message: str = ""


@router.get("/login/qr")
async def get_login_qr():
    """获取登录二维码（直接返回图片）"""
    qrcode_key, content_type, image_data = bili_service.get_login_qr_image()
    if not image_data:
        return {"success": False, "error": "获取二维码失败"}

    return Response(
        content=image_data,
        media_type=content_type,
        headers={"X-QRCode-Key": qrcode_key}
    )


@router.post("/login/poll")
async def poll_login(request: PollLoginRequest):
    """启动登录轮询（后台任务模式，不阻塞）"""
    qrcode_key = request.qrcode_key

    if qrcode_key in login_tasks and not login_tasks[qrcode_key].done():
        return {
            "status": "polling",
            "message": "轮询进行中",
            "qrcode_key": qrcode_key
        }

    login_results[qrcode_key] = {"status": "polling", "success": False, "message": "开始轮询"}

    async def do_poll():
        success, message = await bili_service.wait_login_async(qrcode_key)
        login_results[qrcode_key] = {"status": "done", "success": success, "message": message}

    task = asyncio.create_task(do_poll())
    login_tasks[qrcode_key] = task

    return {
        "status": "polling",
        "message": "轮询已启动",
        "qrcode_key": qrcode_key
    }


@router.get("/login/result/{qrcode_key}")
async def get_login_result(qrcode_key: str):
    """查询登录结果"""
    if qrcode_key not in login_results:
        return {"status": "not_found", "success": False, "message": "未找到登录任务"}

    result = login_results[qrcode_key]

    if result["status"] == "done" and result["success"]:
        if qrcode_key in login_tasks:
            del login_tasks[qrcode_key]
        if qrcode_key in login_results:
            del login_results[qrcode_key]
        return {"success": True, "message": result["message"], "status": "done"}
    elif result["status"] == "done":
        if qrcode_key in login_tasks:
            del login_tasks[qrcode_key]
        if qrcode_key in login_results:
            del login_results[qrcode_key]
        return {"success": False, "message": result["message"], "status": "done"}
    else:
        return {"success": False, "message": result["message"], "status": result["status"]}


@router.get("/status")
async def get_status():
    """获取监控状态"""
    return bili_service.get_status()


@router.get("/ups")
async def get_ups():
    """获取UP主列表"""
    return {"ups": bili_service.get_ups()}


@router.post("/ups")
async def add_up(name: str, uid: str, check_interval: int = 60, enabled: bool = True):
    """添加新的UP主监控"""
    # 验证参数
    if not name or not uid:
        return {"success": False, "message": "名称和UID不能为空"}
    
    if not uid.isdigit():
        return {"success": False, "message": "UID必须是数字"}
    
    if check_interval < 1 or check_interval > 1440:
        return {"success": False, "message": "检查间隔必须在1-1440分钟之间"}
    
    result = bili_service.add_up(name, uid, check_interval, enabled)
    if result:
        return {"success": True, "message": f"成功添加UP主: {name}"}
    else:
        return {"success": False, "message": "UP主已存在"}


@router.delete("/ups/{up_name}")
async def remove_up(up_name: str):
    """移除UP主监控"""
    result = bili_service.remove_up(up_name)
    if result:
        return {"success": True, "message": f"成功移除UP主: {up_name}"}
    else:
        return {"success": False, "message": "UP主不存在"}


@router.post("/ups/{up_name}/toggle")
async def toggle_up(up_name: str):
    """切换UP主启用状态"""
    result = bili_service.toggle_up_enabled(up_name)
    if result:
        config = bili_service.up_configs.get(up_name)
        status = "启用" if config.enabled else "禁用"
        return {"success": True, "message": f"UP主 {up_name} 已{status}"}
    else:
        return {"success": False, "message": "UP主不存在"}


@router.get("/check/{up_name}")
async def check_up(up_name: str):
    """检查单个UP主"""
    images = bili_service.check_up(up_name)
    return {
        "success": True,
        "up_name": up_name,
        "new_count": len(images),
        "images": images
    }


@router.get("/cache/{up_name}")
async def get_cached_images(up_name: str):
    """获取UP主缓存图片"""
    images = bili_service.get_cached_images(up_name)
    return {
        "success": True,
        "up_name": up_name,
        "images": images
    }


@router.get("/check")
async def check_all():
    """检查所有UP主（使用同步版本确保结果一致）"""
    results = await asyncio.to_thread(bili_service.check_all)
    
    total = sum(len(images) for images in results.values())
    
    return {
        "success": True,
        "total_new": total,
        "results": results
    }


@router.post("/config/interval")
async def update_interval(up_name: str, interval_minutes: int):
    """更新UP主检查间隔（分钟）"""
    if up_name not in bili_service.up_configs:
        return {"success": False, "message": "UP主不存在"}
    
    bili_service.update_up_interval(up_name, interval_minutes)
    # 保存配置
    bili_service.save_config(up_intervals={up_name: interval_minutes})
    return {"success": True, "message": "间隔更新成功"}


@router.get("/config")
async def get_config():
    """获取当前配置"""
    config = bili_service.get_config()
    return {"success": True, "config": config}


@router.post("/config")
async def save_config(check_on_start: bool = None):
    """保存配置"""
    bili_service.save_config(check_on_start=check_on_start)
    return {"success": True, "message": "配置保存成功"}


@router.post("/config/scheduler/start")
async def start_scheduler(check_on_start: bool = False):
    """启动定时任务调度器"""
    bili_service.start_scheduler(check_on_start)
    return {"success": True, "message": "调度器已启动"}


@router.post("/config/scheduler/stop")
async def stop_scheduler():
    """停止定时任务调度器"""
    bili_service.stop_scheduler()
    return {"success": True, "message": "调度器已停止"}


@router.get("/config/scheduler/status")
async def get_scheduler_status():
    """获取调度器状态"""
    return {
        "success": True,
        "is_running": bili_service.state.is_running
    }


@router.get("/image/proxy")
async def proxy_image(url: str):
    """
    图片代理接口 - 解决B站图片防盗链问题
    通过后端代理请求B站图片，带上正确的Referer
    """
    if not url.startswith("https://"):
        return {"error": "Invalid URL"}
    
    headers = {
        "Referer": BILI_REFERER,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=15, verify=False)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "image/jpeg")
        
        return StreamingResponse(
            response.iter_content(chunk_size=1024*1024),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename=\"{url.split('/')[-1]}\""
            }
        )
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch image: {str(e)}"}
