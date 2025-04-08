import os
from pathlib import Path
from typing import ClassVar, Dict

import aiohttp
import tomli

from app.logger import logger
from app.tool.base import BaseTool, ToolResult


class WeatherTool(BaseTool):
    """天气查询工具，用于获取指定城市的天气信息"""

    name: str = "weather"
    description: str = (
        "根据城市名称查询当前天气情况，返回温度、湿度、天气状况等信息。建议使用英文城市名（如Beijing而非北京）以获得更准确的结果。"
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "要查询天气的城市名称，推荐使用英文名称，例如：Beijing、Shanghai、Guangzhou等",
            },
            "country_code": {
                "type": "string",
                "description": "国家代码，默认为cn（中国）",
            },
        },
        "required": ["city"],
    }
    api_key: str = ""

    # 常见中文城市名到英文的映射
    CITY_MAP: ClassVar[Dict[str, str]] = {
        "北京": "Beijing",
        "上海": "Shanghai",
        "广州": "Guangzhou",
        "深圳": "Shenzhen",
        "杭州": "Hangzhou",
        "南京": "Nanjing",
        "武汉": "Wuhan",
        "成都": "Chengdu",
        "重庆": "Chongqing",
        "西安": "Xian",
        "天津": "Tianjin",
        "苏州": "Suzhou",
        "厦门": "Xiamen",
        "青岛": "Qingdao",
        "大连": "Dalian",
        "长沙": "Changsha",
        "哈尔滨": "Harbin",
        "沈阳": "Shenyang",
        "济南": "Jinan",
        "郑州": "Zhengzhou",
        "长春": "Changchun",
    }

    def __init__(self, **data):
        """初始化天气工具，加载API密钥"""
        super().__init__(**data)
        self.api_key = self._load_api_key()

    def _load_api_key(self) -> str:
        """从环境变量或配置文件加载API密钥"""
        # 首先尝试从环境变量加载
        api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        if api_key:
            return api_key

        # 然后尝试从配置文件加载
        try:
            config_path = Path("config/config.toml")
            if config_path.exists():
                with open(config_path, "rb") as f:
                    config = tomli.load(f)
                    if "weather" in config and "api_key" in config["weather"]:
                        return config["weather"]["api_key"]
        except Exception as e:
            logger.warning(f"读取配置文件失败: {str(e)}")

        # 默认返回空字符串
        logger.warning(
            "未找到天气API密钥，请在config/config.toml中添加或设置环境变量OPENWEATHERMAP_API_KEY"
        )
        return ""

    def _try_translate_city(self, city: str) -> str:
        """尝试将中文城市名转换为英文"""
        return self.CITY_MAP.get(city, city)

    async def execute(self, city: str, country_code: str = "cn") -> ToolResult:
        """
        执行天气查询

        Args:
            city: 城市名称
            country_code: 国家代码，默认为cn

        Returns:
            ToolResult: 包含天气信息的结果对象
        """
        if not self.api_key:
            return ToolResult(
                error="缺少API密钥，请在config/config.toml的[weather]部分配置api_key"
            )

        try:
            # 确保country_code不为None
            country_code = country_code or "cn"

            # 尝试将中文城市名转换为英文
            english_city = self._try_translate_city(city)
            if english_city != city:
                logger.info(f"将城市名 '{city}' 转换为英文名 '{english_city}'")

            # 构建API请求URL
            url = f"https://api.openweathermap.org/data/2.5/weather?q={english_city},{country_code}&appid={self.api_key}&units=metric&lang=zh_cn"

            logger.info(f"请求天气API: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_data = await response.text()
                        logger.error(f"天气API响应错误: {error_data}")

                        # 如果使用翻译后的城市名仍然失败，且原始名称与翻译后不同，尝试使用原始名称
                        if english_city != city:
                            logger.info(f"尝试使用原始城市名 '{city}' 重新查询")
                            url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country_code}&appid={self.api_key}&units=metric&lang=zh_cn"

                            async with session.get(url) as retry_response:
                                if retry_response.status == 200:
                                    data = await retry_response.json()
                                else:
                                    return ToolResult(
                                        error=f"查询失败，状态码: {response.status}，请尝试使用英文城市名称"
                                    )
                        else:
                            return ToolResult(
                                error=f"查询失败，状态码: {response.status}，请尝试使用英文城市名称"
                            )
                    else:
                        data = await response.json()

                    weather_info = {
                        "城市": f"{data['name']}, {data['sys']['country']}",
                        "天气": data["weather"][0]["description"],
                        "温度": f"{data['main']['temp']}°C",
                        "体感温度": f"{data['main']['feels_like']}°C",
                        "湿度": f"{data['main']['humidity']}%",
                        "风速": f"{data['wind']['speed']} m/s",
                        "云量": f"{data['clouds']['all']}%",
                    }

                    # 格式化输出
                    result = "\n".join([f"{k}: {v}" for k, v in weather_info.items()])
                    return ToolResult(output=result)
        except Exception as e:
            logger.error(f"天气查询错误: {str(e)}")
            return ToolResult(error=f"天气查询出错: {str(e)}")
