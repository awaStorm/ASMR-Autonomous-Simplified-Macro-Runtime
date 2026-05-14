"""点击统计API"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from pathlib import Path
import json
import os

router = APIRouter()

# 数据存储路径
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CLICK_STATS_FILE = DATA_DIR / "click_stats.json"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 页面名称映射
PAGE_NAMES = {
    '/': '首页',
    '/home': '首页',
    '/todo': '待办事项',
    '/image': '图片搜索',
    '/bili': 'B站监控',
    '/jm': '禁漫下载',
    '/miao': '喵呜统计',
    'home': '首页',
    'todo': '待办事项',
    'image': '图片搜索',
    'bili': 'B站监控',
    'jm': '禁漫下载',
    'miao': '喵呜统计',
    'Unknown': '未知页面'
}


class ClickReport(BaseModel):
    start_time: int
    end_time: int
    duration: int
    counts: dict
    user_agent: str
    screen_size: str


class DailyStats(BaseModel):
    date: str
    counts: dict
    total: int
    user_agent: str
    screen_size: str


def load_click_stats():
    """加载点击统计数据"""
    if not CLICK_STATS_FILE.exists():
        return {
            "version": "1.0",
            "daily_stats": [],
            "total_counts": {},
            "report_count": 0
        }
    
    try:
        with open(CLICK_STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载点击统计数据失败: {e}")
        return {
            "version": "1.0",
            "daily_stats": [],
            "total_counts": {},
            "report_count": 0
        }


def save_click_stats(data):
    """保存点击统计数据（原子写入）"""
    import tempfile
    
    try:
        fd, temp_path = tempfile.mkstemp(
            suffix='.json',
            prefix='click_stats_',
            dir=str(DATA_DIR)
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, str(CLICK_STATS_FILE))
            return True
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    except Exception as e:
        print(f"保存点击统计数据失败: {e}")
        return False


@router.post("/report")
async def report_click(request: Request):
    """上报点击统计数据"""
    try:
        data = await request.json()
        
        # 验证数据结构
        report = ClickReport(**data)
        
        # 加载现有数据
        stats = load_click_stats()
        
        # 获取日期（UTC+8）
        date_str = datetime.fromtimestamp(report.end_time / 1000).strftime('%Y-%m-%d')
        
        # 更新每日统计
        daily_found = False
        for daily in stats['daily_stats']:
            if daily['date'] == date_str:
                # 合并counts
                for page, count in report.counts.items():
                    daily['counts'][page] = daily['counts'].get(page, 0) + count
                daily['total'] = sum(daily['counts'].values())
                daily_found = True
                break
        
        if not daily_found:
            stats['daily_stats'].append({
                "date": date_str,
                "counts": dict(report.counts),
                "total": sum(report.counts.values()),
                "user_agent": report.user_agent[:200],
                "screen_size": report.screen_size
            })
        
        # 更新总统计
        for page, count in report.counts.items():
            stats['total_counts'][page] = stats['total_counts'].get(page, 0) + count
        
        # 更新上报次数
        stats['report_count'] += 1
        
        # 保存数据
        save_click_stats(stats)
        
        return {"success": True}
        
    except Exception as e:
        print(f"处理点击上报失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/stats")
async def get_click_stats():
    """获取点击统计数据"""
    stats = load_click_stats()
    return {
        "success": True,
        "data": stats
    }


@router.get("/stats/daily")
async def get_daily_stats(date: str = None):
    """获取每日统计数据"""
    stats = load_click_stats()
    
    if date:
        # 按日期筛选
        daily = next((d for d in stats['daily_stats'] if d['date'] == date), None)
        if daily:
            return {"success": True, "data": daily}
        return {"success": False, "error": "日期不存在"}
    
    return {"success": True, "data": stats['daily_stats']}


@router.get("/stats/total")
async def get_total_stats():
    """获取总统计数据"""
    stats = load_click_stats()
    return {
        "success": True,
        "data": {
            "total_counts": stats['total_counts'],
            "total_clicks": sum(stats['total_counts'].values()),
            "report_count": stats['report_count']
        }
    }


@router.get("/stats/aggregate")
async def get_aggregate_stats(
    granularity: str = Query("week", enum=["year", "month", "week"]),
    direction: str = Query("vertical", enum=["horizontal", "vertical"])
):
    """获取聚合统计数据"""
    stats = load_click_stats()
    daily_stats = stats['daily_stats']
    
    # 计算总点击数
    total_clicks = sum(stats['total_counts'].values())
    
    # 获取当前时间（UTC+8）
    now = datetime.now() + timedelta(hours=8)
    
    result = {
        "total": total_clicks,
        "granularity": granularity,
        "direction": direction,
        "data": [],
        "detail_data": {}
    }
    
    if granularity == "year":
        # 年视图：按月份聚合（最近12个月）
        month_data = {}
        for i in range(12):
            month = now - timedelta(days=i * 30)
            month_key = month.strftime('%Y-%m')
            month_data[month_key] = 0
        
        for daily in daily_stats:
            date = datetime.strptime(daily['date'], '%Y-%m-%d')
            month_key = date.strftime('%Y-%m')
            if month_key in month_data:
                month_data[month_key] += daily['total']
        
        # 按时间正序排列（从左到右：较早的月份 -> 较新的月份）
        sorted_months = sorted(month_data.keys())
        for month_key in sorted_months:
            month_name = datetime.strptime(month_key, '%Y-%m').strftime('%Y.%m')
            result['data'].append({
                "label": month_name,
                "count": month_data[month_key],
                "date": month_key
            })
    
    elif granularity == "month":
        # 月视图：按周聚合（最近4-5周）
        week_data = {}
        for i in range(5):
            # 获取本周一
            monday = (now - timedelta(weeks=i)).date() - timedelta(days=(now.weekday()))
            week_key = monday.strftime('%Y-%m-%d')
            week_data[week_key] = 0
        
        for daily in daily_stats:
            date = datetime.strptime(daily['date'], '%Y-%m-%d')
            # 获取该日期所在周的周一
            week_start = date.date() - timedelta(days=date.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            if week_key in week_data:
                week_data[week_key] += daily['total']
        
        # 按时间正序排列（从左到右：较早的周 -> 较新的周）
        sorted_weeks = sorted(week_data.keys())
        for week_key in sorted_weeks:
            week_start = datetime.strptime(week_key, '%Y-%m-%d')
            week_end = week_start + timedelta(days=6)
            week_label = f"{week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')}"
            result['data'].append({
                "label": week_label,
                "count": week_data[week_key],
                "date": week_key
            })
    
    elif granularity == "week":
        # 周视图：按天聚合（最近7天）
        day_data = {}
        day_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        # 获取最近7天（从今天往前推6天）
        for i in range(7):
            date = now.date() - timedelta(days=6 - i)
            date_str = date.strftime('%Y-%m-%d')
            day_data[date_str] = {
                "count": 0,
                "details": {}
            }
        
        for daily in daily_stats:
            date_str = daily['date']
            if date_str in day_data:
                day_data[date_str]['count'] += daily['total']
                day_data[date_str]['details'] = daily['counts']
        
        # 按时间排序（从早到晚）
        sorted_days = sorted(day_data.keys())
        for i, date_str in enumerate(sorted_days):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            weekday_index = date_obj.weekday()
            result['data'].append({
                "label": day_labels[weekday_index],
                "count": day_data[date_str]['count'],
                "date": date_str
            })
            if day_data[date_str]['details']:
                result['detail_data'][date_str] = day_data[date_str]['details']
    
    return result


def cleanup_old_week_data():
    """清理上周的详细数据（每周一自动调用）"""
    stats = load_click_stats()
    
    # 获取本周一
    now = datetime.now() + timedelta(hours=8)
    this_monday = now.date() - timedelta(days=now.weekday())
    
    # 过滤掉上周及更早的详细数据
    stats['daily_stats'] = [
        daily for daily in stats['daily_stats']
        if datetime.strptime(daily['date'], '%Y-%m-%d').date() >= this_monday
    ]
    
    save_click_stats(stats)
    return True


@router.post("/stats/cleanup")
async def cleanup_stats():
    """手动触发数据清理"""
    success = cleanup_old_week_data()
    return {"success": success}