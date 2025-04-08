# OpenManus 天气查询服务

这是一个基于OpenManus框架开发的天气查询服务，利用现有的MCP（Model Context Protocol）框架提供天气查询功能。

## 功能特点

- 基于OpenWeatherMap API实现天气查询
- 支持全球城市的天气信息获取
- 返回温度、湿度、天气状况等详细信息
- 无缝集成到OpenManus的MCP工具框架中

## 安装配置

1. 确保已安装OpenManus项目和依赖：

```bash
pip install -r requirements.txt
```

2. 获取OpenWeatherMap API密钥：

   - 访问 [OpenWeatherMap](https://openweathermap.org/)
   - 注册并创建免费API密钥

3. 配置API密钥：

   将API密钥添加到配置文件中。有两种方式：

   **方式一：修改现有配置文件**
   - 编辑 `config/config.toml` 文件，添加以下内容：
   ```toml
   [weather]
   api_key = "你的OpenWeatherMap API密钥"
   ```

   **方式二：使用环境变量**
   ```bash
   export OPENWEATHERMAP_API_KEY="你的OpenWeatherMap API密钥"
   ```

## 使用方法

### 方式一：启动天气服务器并使用OpenManus客户端

1. 首先，启动天气MCP服务器：

```bash
python run_weather_server.py
```

2. 然后，在另一个终端使用OpenManus的MCP客户端连接：

```bash
python run_mcp.py
```

3. 在客户端提示符下，可以进行天气查询：

```
查询北京的天气
```

### 方式二：直接在配置中指定天气服务器

1. 将天气服务器配置添加到OpenManus配置中：

   - 将 `config/weather_mcp.toml` 的内容复制到 `config/config.toml`
   - 或者创建一个包含以下内容的新配置：

   ```toml
   [mcp]
   server_reference = "run_weather_server"

   [weather]
   api_key = "你的OpenWeatherMap API密钥"
   ```

2. 直接运行MCP客户端即可：

```bash
python run_mcp.py
```

3. 在客户端提示符下，可以进行天气查询：

```
查询上海的天气情况
今天深圳天气怎么样？
```

## 输出示例

查询结果将类似于以下格式：

```
城市: Beijing, CN
天气: 晴
温度: 25.6°C
体感温度: 24.8°C
湿度: 45%
风速: 3.5 m/s
云量: 10%
```

## 注意事项

- API请求有使用限制，免费账户限制为每分钟60次调用
- 城市名称支持中文，但某些特殊城市可能需要使用英文名称
- 国家代码遵循ISO 3166标准（如中国为"cn"，美国为"us"）
- 查询结果默认为中文（通过API参数lang=zh_cn控制）

## 扩展开发

此实现展示了如何在OpenManus框架中集成自定义工具。如需进一步扩展：

1. 修改 `app/tool/custom/weather.py` 添加更多功能（如天气预报、空气质量查询等）
2. 更新 `run_weather_server.py` 注册新工具
3. 根据需要调整输出格式或添加更多数据源
