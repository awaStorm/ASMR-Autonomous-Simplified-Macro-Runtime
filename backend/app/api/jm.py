"""禁漫 API"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..services.jm_service import jm_service


router = APIRouter()


class JmDownloadRequest(BaseModel):
    album_id: str


@router.post("/download")
async def download(request: JmDownloadRequest):
    """开始下载本子"""
    if not request.album_id.isdigit():
        return {
            "success": False,
            "error": "车牌号必须是数字"
        }
    
    result = await jm_service.start_download(request.album_id)
    return result


@router.get("/status/{album_id}")
async def get_status(album_id: str):
    """获取下载状态"""
    status = jm_service.get_task_status(album_id)
    if status is None:
        # 检查是否已在历史记录中
        pdf_path = jm_service._pdf_path(album_id)
        if pdf_path.exists():
            return {
                "success": True,
                "status": "completed",
                "progress": 100
            }
        return {
            "success": False,
            "error": "任务不存在"
        }
    return {
        "success": True,
        **status
    }


@router.get("/recent")
async def get_recent():
    """获取最近的4个本子"""
    items = jm_service.get_recent()
    return {
        "success": True,
        "items": items
    }


@router.get("/history")
async def get_history():
    """获取历史记录（10个）"""
    items = jm_service.get_history()
    return {
        "success": True,
        "items": items
    }


@router.get("/pdf/{album_id}")
async def get_pdf(album_id: str):
    """下载PDF文件"""
    pdf_path = jm_service._pdf_path(album_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF文件不存在")
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{album_id}.pdf"
    )


@router.get("/cover/{album_id}")
async def get_cover(album_id: str):
    """获取封面图片"""
    cover_path = jm_service._cover_path(album_id)
    if not cover_path.exists():
        raise HTTPException(status_code=404, detail="封面不存在")
    
    return FileResponse(
        path=cover_path,
        media_type="image/jpeg"
    )


@router.delete("/item/{album_id}")
async def delete_item(album_id: str):
    """删除本子及其相关数据"""
    success = jm_service.delete_item(album_id)
    if success:
        return {
            "success": True,
            "message": "删除成功"
        }
    return {
        "success": False,
        "error": "删除失败"
    }
