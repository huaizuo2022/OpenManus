#!/usr/bin/env python
# coding: utf-8
# 基于OpenManus框架的有赞订单查询MCP服务器
from app.logger import logger
from app.mcp.server import MCPServer, parse_args
from app.tool.custom.youzan_order import YouzanOrderTool

if __name__ == "__main__":
    args = parse_args()

    # 创建服务器实例
    server = MCPServer("youzan-order-server")

    # 注册订单查询工具
    server.tools["youzan_order"] = YouzanOrderTool()
    logger.info("已注册有赞订单查询工具")

    # 运行服务器
    logger.info(f"启动有赞订单查询MCP服务器（{args.transport}模式）")
    server.run(transport=args.transport)
