# ASMR

自简宏枢 - 将 QQ 机器人插件迁移到 Web 应用，保留业务逻辑，去除 QQ 依赖。

## 端口配置

| 服务 | 端口 | 配置位置 |
|------|------|----------|
| 后端 API | 8137 | `backend/app/config.py` |
| 前端开发服务器 | 5173 | `frontend/vite.config.js` |
| 前端代理目标 | `http://localhost:8137` | `frontend/vite.config.js` |

**注意**：前后端端口必须保持一致，前端通过代理 `/api` 请求到后端。

## 环境要求

- **Python**: 3.11+（注意：如果系统有多个 Python 版本，需要指定 Python 3.11）
- **Node.js**: 18+

## 项目架构

```
ASMR/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/     # API 路由
│   │   ├── services/ # 业务逻辑
│   │   ├── plugins/  # 插件接口（保留接口定义）
│   │   ├── models.py # SQLAlchemy 模型
│   │   ├── database.py # 数据库配置
│   │   ├── config.py   # 应用配置
│   │   └── main.py  # FastAPI 入口
│   ├── config/      # 配置文件
│   ├── data/        # 数据存储
│   └── requirements.txt
├── frontend/         # Vue 3 前端
│   ├── src/
│   │   ├── views/   # 页面视图
│   │   ├── components/ # 组件
│   │   ├── api/     # API 调用
│   │   ├── router/  # 路由配置
│   │   └── composables/ # 组合式函数
│   └── package.json
├── data/             # 外部数据目录
│   └── jm/          # 禁漫数据
├── scripts/
│   └── migrate_db.py # 数据库迁移脚本
└── docker-compose.yml
```

## 功能模块

### 已实现功能

- **主页** - 显示一言随机语录，带打字机动画效果
- **待办事项** - 待办列表的增删改查，支持优先级排序和状态筛选
- **图片搜索** - 基于图片内容的搜索功能
- **B站监控** - 监控 B 站 UP 主更新并推送通知
- **禁漫下载** - 下载和管理 COMIC 资源
- **喵喵喵** - 娱乐模块
- **设置** - 应用主题和配置管理

### 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + Vite + TailwindCSS + Lucide 图标
- **图表**: ECharts
- **动画**: Anime.js

## 快速开始

### 1. 数据库准备

数据库文件位于 `backend/data/todos.db`，首次启动时会自动创建表结构。

如需从旧版 QQ 机器人迁移数据，可使用迁移脚本（需要提供旧数据库路径）：

```powershell
# 默认从 backend/data/todos.db 读取（已迁移后的位置）
python scripts/migrate_db.py

# 如需从其他位置迁移（如旧版插件数据库）
python scripts/migrate_db.py /path/to/old/todos.db
```

### 2. 启动后端

```powershell
cd backend

# 创建虚拟环境（仅首次）
py -3.11 -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --reload --port 8137
```

后端会在 http://localhost:8137 启动

访问 http://localhost:8137/docs 查看 API 文档

### 3. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端会在 http://localhost:5173 启动

## 常见问题

### Python 版本问题

如果系统有多个 Python 版本（如 3.13 和 3.11），使用 `py -3.11` 命令指定版本：

```powershell
# 查看可用 Python 版本
py -0

# 使用指定版本创建虚拟环境
py -3.11 -m venv venv
```

## API 端点

| 路径 | 描述 |
|------|------|
| `/api/todos` | 待办事项 CRUD |
| `/api/images` | 图片搜索 |
| `/api/bili` | B站监控 |
| `/api/jm` | 禁漫下载 |
| `/api/agent` | 智能代理 |
| `/api/click` | 点击统计 |
