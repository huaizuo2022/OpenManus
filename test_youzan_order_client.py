#!/usr/bin/env python
# coding: utf-8
# 测试有赞订单查询MCP客户端

import asyncio
import os
import sys

os.environ["LOG_LEVEL"] = "INFO"

from app.tool.mcp import MCPClients


async def main():
    print("========================")
    print("有赞订单查询测试客户端")
    print("========================")

    # 创建MCP客户端
    mcp_client = MCPClients()

    # 获取Python解释器路径
    python_executable = sys.executable

    # 连接到服务器
    print("正在连接到服务器...")
    try:
        await mcp_client.connect_stdio(
            python_executable, ["run_youzan_order_server.py"]
        )
        print("连接成功!")

        # 打印可用工具
        print("\n可用工具列表:")
        for tool in mcp_client.tools:
            print(f" - {tool.name}: {tool.description}")

        # 测试订单查询
        order_no = input(
            "\n请输入要查询的订单号 (默认E20241127175508087302012): "
        ).strip()
        if not order_no:
            order_no = "E20241127175508087302012"

        print(f"\n正在查询订单: {order_no}")

        # 查找有赞订单工具
        youzan_tool = None
        for tool in mcp_client.tools:
            if tool.name == "youzan_order":
                youzan_tool = tool
                break

        if youzan_tool:
            result = await youzan_tool.execute(order_no=order_no)
            print("\n查询结果:")
            print(result)
        else:
            print("\n错误: 未找到有赞订单查询工具!")

    except Exception as e:
        print(f"连接失败: {str(e)}")
    finally:
        # 断开连接
        if hasattr(mcp_client, "disconnect"):
            await mcp_client.disconnect()
        print("\n已断开连接")


if __name__ == "__main__":
    asyncio.run(main())
