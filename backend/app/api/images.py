"""图片搜索API"""
from fastapi import APIRouter, Query
from fastapi.responses import Response
from typing import List, Optional
import httpx

from ..services.image_service import ImageService

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
