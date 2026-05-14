from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]] = []


@router.get("/tools", response_model=List[ToolDefinition])
async def get_tools():
    """获取所有可用工具定义（MCP格式）"""
    tools = [
        ToolDefinition(
            name="todo_create",
            description="创建一个新的待办事项",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "待办内容"},
                    "priority": {"type": "integer", "enum": [3, 2, 1], "description": "优先级: 3=高, 2=中, 1=低"},
                    "deadline": {"type": "string", "description": "截止时间，格式：1d2h（1天2小时）或 ISO 格式"}
                },
                "required": ["content", "priority", "deadline"]
            }
        ),
        ToolDefinition(
            name="todo_list",
            description="获取待办事项列表",
            input_schema={
                "type": "object",
                "properties": {
                    "completed": {"type": "boolean", "description": "只返回完成/未完成的待办"}
                }
            }
        ),
        ToolDefinition(
            name="todo_complete",
            description="标记待办事项为完成",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "待办事项ID"}
                },
                "required": ["id"]
            }
        ),
        ToolDefinition(
            name="todo_delete",
            description="删除待办事项",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "待办事项ID"}
                },
                "required": ["id"]
            }
        )
    ]
    return tools


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Agent对话接口（Mock版本，供未来接入）"""
    return ChatResponse(
        response=f"收到消息: {request.message}\n（此接口为Mock，等待真实Agent实现）",
        tool_calls=[]
    )
