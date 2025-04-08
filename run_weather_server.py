#!/usr/bin/env python
# coding: utf-8
# 基于OpenManus框架的天气查询MCP服务器
from app.logger import logger
from app.mcp.server import MCPServer, parse_args
from app.tool.custom.weather import WeatherTool

if __name__ == "__main__":
    args = parse_args()

    # 创建服务器实例
    server = MCPServer("weather-server")

    # 注册天气查询工具
    server.tools["weather"] = WeatherTool()
    logger.info("已注册天气查询工具")

    # 运行服务器
    logger.info(f"启动天气查询MCP服务器（{args.transport}模式）")
    server.run(transport=args.transport)
