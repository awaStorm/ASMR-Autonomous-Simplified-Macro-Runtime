from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseTool(ABC):
    """所有插件的统一抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        返回工具定义列表（MCP工具格式）
        用于 /api/agent/tools 接口
        """
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        调用具体工具
        :param tool_name: 工具名称
        :param arguments: 工具参数
        :return: 工具执行结果
        """
        pass
