import asyncio
import os
import sys
import tomllib
from pathlib import Path
from typing import List, Optional

from app.logger import logger
from app.tool.mcp import MCPClients


class MCPConnector:
    """MCP连接器，用于连接MCP服务器并获取工具"""

    def __init__(self):
        self.mcp_clients = {}

    async def connect_to_server(self, server_ref: str) -> Optional[MCPClients]:
        """连接到指定的MCP服务器

        Args:
            server_ref: 服务器引用（模块名或脚本路径）

        Returns:
            MCPClients或None（如果连接失败）
        """
        try:
            # 创建MCP客户端
            mcp_client = MCPClients()

            # 获取项目根目录
            project_root = Path(__file__).parent.parent

            # 构建完整的脚本路径
            script_path = f"{server_ref}"
            if not script_path.endswith(".py"):
                script_path = f"{script_path}.py"

            # 构建完整路径
            full_path = project_root / script_path

            # 检查文件是否存在
            if not full_path.exists():
                raise FileNotFoundError(f"服务器脚本文件不存在: {full_path}")

            # 使用当前Python解释器路径
            python_executable = sys.executable
            # 构建命令和参数，分开为列表
            cmd = python_executable
            args = [str(full_path)]

            # 切换当前工作目录到项目根目录
            original_cwd = os.getcwd()
            os.chdir(str(project_root))

            try:
                # 连接到服务器
                logger.info(
                    f"连接MCP服务器: {cmd} {' '.join(args)} (在目录 {project_root})"
                )
                await mcp_client.connect_stdio(cmd, args)

                # 存储客户端引用
                self.mcp_clients[server_ref] = mcp_client

                # 记录连接的工具
                logger.info(
                    f"已连接到MCP服务器: {server_ref}，工具列表: {[tool.name for tool in mcp_client.tools]}"
                )
                return mcp_client
            finally:
                # 恢复原始工作目录
                os.chdir(original_cwd)
        except Exception as e:
            logger.error(f"连接MCP服务器失败 {server_ref}: {str(e)}")
            return None

    async def connect_to_youzan_order_server(self) -> Optional[MCPClients]:
        """专门连接到有赞订单服务器

        Returns:
            MCPClients或None（如果连接失败）
        """
        try:
            # 查找配置文件中的有赞订单服务器引用
            config_path = Path(__file__).parent.parent / "config" / "config.toml"
            server_ref = "run_youzan_order_server"  # 默认值

            if config_path.exists():
                try:
                    with open(config_path, "rb") as f:
                        config_data = tomllib.load(f)

                    if (
                        "mcp" in config_data
                        and "server_reference" in config_data["mcp"]
                    ):
                        ref = config_data["mcp"]["server_reference"]
                        if "youzan" in ref.lower() or "order" in ref.lower():
                            server_ref = ref
                except Exception as e:
                    logger.warning(f"读取配置文件失败: {str(e)}")

            # 连接到有赞订单服务器
            logger.info(f"尝试连接有赞订单服务器: {server_ref}")
            return await self.connect_to_server(server_ref)
        except Exception as e:
            logger.error(f"连接有赞订单服务器失败: {str(e)}")
            return None

    async def get_all_tools(self) -> List:
        """获取所有已连接服务器的工具列表

        Returns:
            工具列表
        """
        tools = []
        for client in self.mcp_clients.values():
            tools.extend(client.tools)
        return tools

    async def disconnect_all(self):
        """断开所有MCP连接"""
        for server_ref, client in self.mcp_clients.items():
            try:
                logger.info(f"断开MCP服务器连接: {server_ref}")
                await client.disconnect()
            except Exception as e:
                logger.warning(f"断开MCP服务器连接失败 {server_ref}: {str(e)}")

        # 清空客户端字典
        self.mcp_clients = {}


# 单例实例
connector = MCPConnector()
