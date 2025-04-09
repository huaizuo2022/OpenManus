# OpenManus 有赞订单查询服务

这是一个基于OpenManus框架开发的有赞订单查询服务，利用现有的MCP（Model Context Protocol）框架提供订单查询功能。

## 功能特点

- 基于有赞订单API实现订单查询
- 根据订单号获取详细的订单信息
- 返回订单状态、支付信息、商品明细等完整数据
- 无缝集成到OpenManus的MCP工具框架中

## 安装配置

确保已安装OpenManus项目和依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 方式一：启动订单查询服务器并使用OpenManus客户端

1. 首先，启动有赞订单查询MCP服务器：

```bash
python run_youzan_order_server.py
```

2. 然后，在另一个终端使用OpenManus的MCP客户端连接：

```bash
python run_mcp.py
```

3. 在客户端提示符下，可以进行订单查询：

```
查询订单号E20241127175508087302012的详细信息
```

### 方式二：直接在配置中指定订单查询服务器

1. 将订单查询服务器配置添加到OpenManus配置中：

   - 将 `config/youzan_order_mcp.toml` 的内容复制到 `config/config.toml`
   - 或者创建一个包含以下内容的新配置：

   ```toml
   [mcp]
   server_reference = "run_youzan_order_server"
   ```

2. 直接运行MCP客户端即可：

```bash
python run_mcp.py
```

3. 在客户端提示符下，可以进行订单查询：

```
查询订单E20241127175508087302012的详情
```

## 输出示例

查询结果将类似于以下格式：

```
订单号: E20241127175508087302012
状态: 已支付
创建时间: 2024-11-27 17:55:08

支付方式: 微信支付
支付状态: 已支付
支付金额: ¥199.00

商品信息:
  1. iPhone 15 Pro 128GB
     单价: ¥6999.00
     数量: 1
     总价: ¥6999.00

买家信息:
  买家ID: 12345678
  买家名: 张三

备注: 请尽快发货，谢谢！
```

## 注意事项

- 该服务仅限内部使用，API地址不应暴露在公网环境
- 订单查询API可能有访问频率限制
- 订单号格式必须正确，否则会返回查询失败

## 扩展开发

此实现展示了如何在OpenManus框架中集成自定义工具。如需进一步扩展：

1. 修改 `app/tool/custom/youzan_order.py` 添加更多功能（如创建订单、取消订单等）
2. 更新 `run_youzan_order_server.py` 注册新工具
3. 根据需要调整输出格式或添加更多字段
