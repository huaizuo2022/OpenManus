#!/usr/bin/env python
# coding: utf-8
# 基于OpenManus框架的有赞订单查询MCP服务器
import logging
import os
import sys

# 设置日志级别为INFO以显示更多信息
os.environ["LOG_LEVEL"] = "INFO"
logging.basicConfig(level=logging.INFO)

from app.logger import logger
from app.mcp.server import MCPServer, parse_args
from app.tool.custom.youzan_order import YouzanOrderTool

if __name__ == "__main__":
    # 打印明确的启动信息
    print("========================")
    print("有赞订单查询MCP服务器启动中...")
    print("========================")

    args = parse_args()

    # 创建服务器实例
    server = MCPServer("youzan-order-server")

    # 注册订单查询工具
    server.tools["youzan_order"] = YouzanOrderTool()
    logger.info("已注册有赞订单查询工具")

    # 打印启动确认信息
    print(f"服务器模式: {args.transport}")
    print("服务器已启动，等待连接...")
    print("按Ctrl+C终止服务器")
    print("========================")

    # 运行服务器
    logger.info(f"启动有赞订单服务器（{args.transport}模式）")

    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"\n服务器启动异常: {str(e)}")
