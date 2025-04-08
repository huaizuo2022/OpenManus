#!/usr/bin/env python
# coding: utf-8
# 自定义MCP服务器 - 天气查询服务
import argparse
import asyncio

from app.logger import logger
from app.mcp.server import MCPServer
from app.tool.custom.weather import WeatherTool


class WeatherMCPServer(MCPServer):
    """扩展的MCP服务器，集成了天气查询功能"""

    def __init__(self, name: str = "weather-server"):
        # 初始化基础MCP服务器
        super().__init__(name)

        # 添加天气查询工具
        self.tools["weather"] = WeatherTool()
        logger.info("已注册天气查询工具")


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="天气查询MCP服务器")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="通信方式: stdio或http (默认: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP服务器端口 (仅当transport=http时有效)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # 创建并运行天气服务器
    logger.info("启动天气查询MCP服务器")
    server = WeatherMCPServer()

    # 设置API密钥环境变量（可选，更好的做法是使用配置文件）
    # import os
    # os.environ["OPENWEATHERMAP_API_KEY"] = "你的API密钥"

    # 运行服务器
    if args.transport == "http":
        # 如果FastMCP支持HTTP模式，则使用以下代码
        server.run(transport=args.transport, port=args.port)
    else:
        # 标准stdio模式
        server.run(transport=args.transport)
