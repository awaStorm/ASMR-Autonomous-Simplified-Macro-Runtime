"""图片搜索API"""
from fastapi import APIRouter, Query, Form
from fastapi.responses import Response
from typing import List, Optional, Dict
import httpx

from ..services.image_service import (
    ImageService, check_api_config, API_REQUIREMENTS, PRESET_API_URLS,
    set_api_key, get_saved_api_keys
)

router = APIRouter()
image_service = ImageService()


@router.get("/search", response_model=List[str])
async def search_images(
    keyword: str,
    count: int = Query(3, ge=1, le=10),
    source: Optional[str] = Query("baidu", enum=["baidu", "pexels", "cat", "lolicon"]),
    r18: Optional[int] = Query(0, ge=0, le=1)
):
    """搜索图片"""
    urls = await image_service.search_images(keyword, count, source, r18)
    return urls


@router.get("/cat", response_model=List[str])
async def get_cat_images(count: int = Query(3, ge=1, le=100)):
    """获取随机猫图 - 最多100张"""
    urls = await image_service.get_cat_images(count)
    return urls


@router.get("/lolicon", response_model=List[str])
async def get_lolicon_images(
    keyword: str = "",
    count: int = Query(3, ge=1, le=10),
    r18: Optional[int] = Query(0, ge=0, le=1)
):
    """获取Lolicon二次元图片"""
    urls = await image_service.get_lolicon_images(keyword, count, r18)
    return urls


@router.get("/stats")
async def get_stats():
    """获取图片搜索统计信息"""
    return image_service.get_stats()


@router.get("/proxy")
async def proxy_image(url: str):
    """代理图片请求，解决跨域问题"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            return Response(
                content=response.content,
                media_type=response.headers.get("content-type", "image/jpeg"),
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=86400"
                }
            )
    except Exception as e:
        return Response(content=str(e), status_code=500)


@router.get("/config/status")
async def get_config_status() -> Dict[str, Dict]:
    """获取各图片源的配置状态"""
    status = {}
    saved_keys = get_saved_api_keys()

    for source in API_REQUIREMENTS.keys():
        errors = check_api_config(source)
        has_saved_key = source in saved_keys and (
            saved_keys[source].get('api_key') or saved_keys[source].get('user_id')
        )

        status[source] = {
            'configured': len(errors) == 0,
            'errors': errors,
            'requires_key': API_REQUIREMENTS[source]['needs_key'],
            'requires_user_id': API_REQUIREMENTS[source]['needs_user_id'],
            'api_url': PRESET_API_URLS[source],
            'has_saved_key': has_saved_key
        }
    return status


@router.post("/config/set")
async def set_api_config_api(
    source: str = Form(...),
    api_key: str = Form(""),
    user_id: str = Form("")
):
    """设置图片源的 API 密钥（持久化到文件）"""
    if source not in API_REQUIREMENTS:
        return {"success": False, "message": "未知的图片源"}

    success = set_api_key(source, api_key, user_id)

    if success:
        return {"success": True, "message": "配置已保存", "source": source}
    else:
        return {"success": False, "message": "保存失败"}


@router.get("/config/requirements")
async def get_api_requirements() -> Dict[str, Dict]:
    """获取各图片源的配置要求"""
    requirements = {}
    for source, req in API_REQUIREMENTS.items():
        requirements[source] = {
            'needs_key': req['needs_key'],
            'needs_user_id': req['needs_user_id'],
            'needs_url': req['needs_url'],
            'api_url': PRESET_API_URLS[source]
        }
    return requirements
