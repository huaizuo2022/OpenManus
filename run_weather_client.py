#!/usr/bin/env python
# coding: utf-8
# 天气查询MCP客户端
import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

from app.logger import logger
from app.tool.mcp import MCPClients


async def main():
    """主函数，连接MCP服务器并进行天气查询"""
    parser = argparse.ArgumentParser(description="天气查询客户端")
    parser.add_argument("--city", type=str, help="要查询的城市", default="")
    parser.add_argument("--country", type=str, help="国家代码", default="cn")
    args = parser.parse_args()

    # 创建MCP客户端工具集合
    mcp_tools = MCPClients()

    # 启动MCP服务器进程
    server_path = Path("run_weather_mcp_server.py")
    if not server_path.exists():
        logger.error(f"找不到服务器脚本: {server_path}")
        sys.exit(1)

    logger.info("启动天气MCP服务器...")
    server_process = subprocess.Popen(
        [sys.executable, str(server_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # 连接到服务器
        await mcp_tools.connect_stdio(sys.executable, [str(server_path)])
        logger.info("已连接到天气MCP服务器")

        if not args.city:
            # 交互式模式
            while True:
                city = input("请输入要查询的城市名称（输入q退出）: ")
                if city.lower() == "q":
                    break

                country = (
                    input(f"请输入国家代码（默认为{args.country}）: ") or args.country
                )

                # 调用天气查询工具
                if "weather" in mcp_tools.tool_map:
                    weather_tool = mcp_tools.tool_map["weather"]
                    result = await weather_tool.execute(city=city, country_code=country)

                    if result.error:
                        logger.error(f"查询失败: {result.error}")
                    else:
                        print(f"\n===== {city}的天气情况 =====")
                        print(result.output)
                        print("=======================\n")
                else:
                    logger.error("未找到天气查询工具")
                    break
        else:
            # 命令行参数模式
            if "weather" in mcp_tools.tool_map:
                weather_tool = mcp_tools.tool_map["weather"]
                result = await weather_tool.execute(
                    city=args.city, country_code=args.country
                )

                if result.error:
                    logger.error(f"查询失败: {result.error}")
                else:
                    print(f"\n===== {args.city}的天气情况 =====")
                    print(result.output)
                    print("=======================\n")
            else:
                logger.error("未找到天气查询工具")

    finally:
        # 关闭连接和服务器
        await mcp_tools.disconnect()
        if server_process:
            server_process.terminate()
            server_process.wait()
            logger.info("已关闭天气MCP服务器")


if __name__ == "__main__":
    asyncio.run(main())
