# 快速启动指南

## 环境要求

- **Python**: 3.11（注意：如果系统有多个 Python 版本，需要指定 Python 3.11）
- **Node.js**: 18+

## 步骤 1: 数据库准备

数据库文件位于 `backend/data/todos.db`，首次启动时会自动创建表结构。

如需从旧版 QQ 机器人迁移数据：

```powershell
# 在项目根目录运行
python scripts/migrate_db.py /path/to/old/todos.db
```

## 步骤 2: 启动后端（使用虚拟环境）

```powershell
cd backend

# 创建虚拟环境（仅首次）
# 如果系统有多个 Python 版本，使用 py -3.11 或指定完整路径
py -3.11 -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --reload
```

后端会在 http://localhost:8137 启动

访问 http://localhost:8137/docs 查看 API 文档

## 步骤 3: 启动前端

打开一个新终端窗口：

```powershell
cd frontend
npm install
npm run dev
```

前端会在 http://localhost:5173 启动

## 常见问题

### Python 版本问题

如果系统有多个 Python 版本（ 如 3.13 和 3.11），使用 `py -3.11` 命令指定版本：

```powershell
# 查看可用 Python 版本
py -0

# 使用指定版本创建虚拟环境
py -3.11 -m venv venv
```

## 功能说明

### 已实现功能
- ✅ 待办列表展示（按优先级排序）
- ✅ 创建新待办
- ✅ 标记完成
- ✅ 删除待办
- ✅ 统计信息展示
- ✅ 筛选（全部/进行中/已完成）
- ✅ 图片搜索 (ImageView)
- ✅ B站监控 (BiliView)
- ✅ 禁漫下载 (JmView)
- ✅ Agent 智能对话
- ✅ 喵喵喵娱乐模块 (MiaoView)

## 插件接口标准

所有插件需实现 `BaseTool` 接口：

```python
from app.base_tool import BaseTool

class YourPlugin(BaseTool):
    async def execute(self, *args, **kwargs):
        # 插件逻辑
        pass
```
