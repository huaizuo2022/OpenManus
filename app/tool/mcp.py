from contextlib import AsyncExitStack
from typing import List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from app.logger import logger
from app.tool.base import BaseTool, ToolResult
from app.tool.tool_collection import ToolCollection


class MCPClientTool(BaseTool):
    """Represents a tool proxy that can be called on the MCP server from the client side."""

    session: Optional[ClientSession] = None

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool by making a remote call to the MCP server."""
        if not self.session:
            return ToolResult(error="Not connected to MCP server")

        try:
            result = await self.session.call_tool(self.name, kwargs)
            content_str = ", ".join(
                item.text for item in result.content if isinstance(item, TextContent)
            )
            return ToolResult(output=content_str or "No output returned.")
        except Exception as e:
            return ToolResult(error=f"Error executing tool: {str(e)}")


class MCPClients(ToolCollection):
    """
    A collection of tools that connects to an MCP server and manages available tools through the Model Context Protocol.
    """

    session: Optional[ClientSession] = None
    exit_stack: AsyncExitStack = None
    description: str = "MCP client tools for server interaction"

    def __init__(self):
        """MCPClients类的构造函数

        功能：
        - 初始化工具集合
        - 设置默认名称
        - 创建异步退出栈

        继承：
            ToolCollection: 基础工具集合类
        """
        # 调用父类构造函数初始化空工具列表
        super().__init__()
        # 设置工具集合名称(保持向后兼容)
        self.name = "mcp"
        # 创建异步退出栈用于资源管理
        self.exit_stack = AsyncExitStack()

    async def connect_sse(self, server_url: str) -> None:
        """Connect to an MCP server using SSE transport.

        Args:
            server_url: MCP服务器的URL地址

        Raises:
            ValueError: 当server_url为空时抛出
        """
        # 检查服务器URL是否有效
        if not server_url:
            raise ValueError("Server URL is required.")

        # 如果已有活跃连接，先断开旧连接
        if self.session:
            await self.disconnect()

        # 创建SSE客户端连接上下文
        streams_context = sse_client(url=server_url)
        # 通过异步上下文管理器建立连接
        streams = await self.exit_stack.enter_async_context(streams_context)
        # 初始化客户端会话
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(*streams)  # 使用解包操作符传递流对象
        )

        # 初始化工具列表
        await self._initialize_and_list_tools()

    async def connect_stdio(self, command: str, args: List[str]) -> None:
        """通过标准输入输出(stdio)连接到MCP服务器

        功能：
        - 建立与MCP服务器的stdio连接
        - 初始化会话并获取工具列表

        参数：
            command: 要执行的服务器命令
            args: 命令参数列表

        异常：
            ValueError: 当command为空时抛出
        """
        # 检查必须的命令参数
        if not command:
            raise ValueError("Server command is required.")

        # 如果已有活跃连接，先断开旧连接
        if self.session:
            await self.disconnect()

        # 创建标准IO服务器参数配置
        server_params = StdioServerParameters(command=command, args=args)
        # 通过异步上下文管理器建立stdio传输通道
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)  # 创建stdio客户端连接
        )

        # 获取读写流对象
        read, write = stdio_transport
        # 初始化客户端会话
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)  # 传入读写流创建会话
        )

        # 初始化工具列表
        await self._initialize_and_list_tools()

    async def _initialize_and_list_tools(self) -> None:
        """初始化会话并填充工具映射表

        功能：
        - 初始化MCP会话
        - 从服务器获取工具列表
        - 创建本地工具代理对象
        - 更新工具集合

        异常：
            RuntimeError: 当会话未初始化时抛出
        """
        # 检查会话是否已初始化
        if not self.session:
            raise RuntimeError("Session not initialized.")

        # 初始化MCP会话
        await self.session.initialize()
        # 从服务器获取工具列表响应
        response = await self.session.list_tools()

        # 清空现有工具集合
        self.tools = tuple()  # 使用空元组重置工具列表
        self.tool_map = {}  # 清空工具映射字典

        # 为每个服务器工具创建代理对象
        for tool in response.tools:
            server_tool = MCPClientTool(
                name=tool.name,  # 工具名称
                description=tool.description,  # 工具描述
                parameters=tool.inputSchema,  # 工具输入参数模式
                session=self.session,  # 共享会话实例
            )
            # 将工具添加到映射表
            self.tool_map[tool.name] = server_tool

        # 更新工具元组
        self.tools = tuple(self.tool_map.values())
        # 记录连接成功的日志信���
        logger.info(
            f"Connected to server with tools: {[tool.name for tool in response.tools]}"
        )

    async def disconnect(self) -> None:
        """Disconnect from the MCP server and clean up resources."""
        if self.session and self.exit_stack:
            await self.exit_stack.aclose()
            self.session = None
            self.tools = tuple()
            self.tool_map = {}
            logger.info("Disconnected from MCP server")
