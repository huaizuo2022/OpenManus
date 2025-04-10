import json
from datetime import datetime
from typing import ClassVar, Dict, List

import aiohttp

from app.logger import logger
from app.tool.base import BaseTool, ToolResult


class YouzanOrderTool(BaseTool):
    """有赞订单查询工具，用于获取订单详细信息"""

    name: str = "youzan_order"
    description: str = (
        "根据订单号查询有赞订单详细信息，返回包含商品、支付等详情的订单信息。"
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "order_no": {
                "type": "string",
                "description": "要查询的订单号，例如：E20241127175508087302012",
            }
        },
        "required": ["order_no"],
    }

    # API配置
    API_URL: ClassVar[str] = (
        "http://tether-qa.s.qima-inc.com:8680/soa/com.youzan.trade.detail.api.service.OrderDetailService/getOrders"
    )
    HEADERS: ClassVar[Dict[str, str]] = {
        "Content-Type": "application/json",
        "x-request-protocol": "dubbo",
        "X-Timeout": "10000",
        "X-Service-Chain": "{}",
    }

    async def execute(self, order_no: str) -> ToolResult:
        """
        执行订单查询

        Args:
            order_no: 订单号

        Returns:
            ToolResult: 包含订单信息的结果对象
        """
        logger.warning(f"====== 开始查询订单: {order_no} ======")
        try:
            # 构建请求参数
            request_id = self._generate_request_id()
            payload = [
                {
                    "app": "trade-plugin",
                    "bizGroup": "trade",
                    "options": {
                        "withBuyerInfo": True,
                        "withCustomInfo": False,
                        "withDeliveryInfo": False,
                        "withFulfillOrderInfo": False,
                        "withItemInfo": True,
                        "withMainOrderInfo": True,
                        "withMultiPeriodPlanInfo": False,
                        "withOrderAddressInfo": False,
                        "withPaymentInfo": True,
                        "withPromotionInfo": False,
                        "withRefundInfo": False,
                        "withRemark": True,
                        "withSourceInfo": False,
                    },
                    "orderNos": [order_no],
                    "requestId": request_id,
                }
            ]

            # 记录请求参数
            logger.debug(f"查询订单：{order_no}, 请求参数: {json.dumps(payload)}")
            logger.debug(f"请求URL: {self.API_URL}")
            logger.debug(f"请求头: {self.HEADERS}")

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    headers=self.HEADERS,
                    data=json.dumps(payload),
                    timeout=12,  # 设置比X-Timeout稍长的超时时间
                ) as response:
                    logger.info(f"HTTP响应状态码: {response.status}")

                    # 读取响应内容
                    raw_response = await response.text()

                    # 为了帮助调试，添加前50个字符的日志
                    preview = (
                        raw_response[:50] + "..."
                        if len(raw_response) > 50
                        else raw_response
                    )
                    logger.debug(f"HTTP响应预览: {preview}")

                    # 保存完整响应到文件，便于后续分析
                    try:
                        with open(
                            f"youzan_order_response_{order_no}.json",
                            "w",
                            encoding="utf-8",
                        ) as f:
                            f.write(raw_response)
                        logger.debug(
                            f"已保存完整响应到文件: youzan_order_response_{order_no}.json"
                        )
                    except Exception as e:
                        logger.warning(f"保存响应到文件失败: {str(e)}")

                    if response.status != 200:
                        error_msg = f"查询失败，状态码: {response.status}"
                        logger.error(f"订单API响应错误: {raw_response}")
                        logger.warning(f"====== 订单查询结束: {error_msg} ======")
                        return ToolResult(error=error_msg)

                    try:
                        data = json.loads(raw_response)
                        # 只记录数据类型，避免日志过大
                        logger.debug(f"解析后的响应数据类型: {type(data)}")
                    except json.JSONDecodeError as e:
                        error_msg = f"响应数据不是有效的JSON格式: {str(e)}"
                        logger.error(
                            f"JSON解析错误: {str(e)}, 原始内容: {raw_response}"
                        )
                        logger.warning(f"====== 订单查询结束: {error_msg} ======")
                        return ToolResult(error=error_msg)

                    # 处理响应
                    result = self._process_response(order_no, data)
                    if result.error:
                        logger.warning(f"====== 订单查询结束: {result.error} ======")
                    else:
                        logger.warning(f"====== 订单查询成功完成 ======")
                    return result
        except Exception as e:
            error_msg = f"订单查询出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            logger.warning(f"====== 订单查询结束: {error_msg} ======")
            return ToolResult(error=error_msg)

    def _generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid

        return str(uuid.uuid4())

    def _process_response(self, order_no: str, data: Dict) -> ToolResult:
        """处理API响应数据，格式化输出"""
        try:
            # 记录详细的数据结构进行诊断
            try:
                with open(
                    f"youzan_order_processed_{order_no}.json", "w", encoding="utf-8"
                ) as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.debug(
                    f"已保存处理后的数据到文件: youzan_order_processed_{order_no}.json"
                )
            except Exception as e:
                logger.warning(f"保存处理后数据到文件失败: {str(e)}")

            # 检查是否有错误响应
            logger.debug(f"开始处理响应数据: 类型={type(data)}")

            if not data:
                logger.error("响应数据为空")
                return ToolResult(error=f"未找到订单 {order_no} 或返回数据为空")

            # 适应字典和列表两种格式的返回数据
            response_data = None
            if isinstance(data, list):
                # 原来期望的列表格式
                if not data[0]:
                    logger.error("响应数据列表第一项为空")
                    return ToolResult(
                        error=f"未找到订单 {order_no} 或返回数据第一项为空"
                    )
                response_data = data[0]
            elif isinstance(data, dict):
                # 实际返回的字典格式
                response_data = data
            else:
                logger.error(f"响应数据既不是字典也不是列表类型，而是 {type(data)}")
                return ToolResult(error=f"返回数据格式不支持: {type(data)}")

            # 记录第一层键
            logger.debug(f"响应数据顶层键列表: {list(response_data.keys())}")

            # 首先检查API是否返回成功
            is_success = False
            if "success" in response_data:
                logger.debug(f"API响应success字段: {response_data['success']}")
                if response_data["success"] is True:
                    is_success = True

            if "code" in response_data:
                logger.debug(f"API响应code字段: {response_data['code']}")
                if response_data["code"] == 200:
                    is_success = True

            if "statusCode" in response_data:
                logger.debug(f"API响应statusCode字段: {response_data['statusCode']}")
                if response_data["statusCode"] == 200:
                    is_success = True

            # 检查是否有错误信息 - 只处理明确的错误信息
            error_message = None
            if not is_success:
                if "errorMessage" in response_data and response_data["errorMessage"]:
                    error_message = response_data["errorMessage"]
                elif "error" in response_data and response_data["error"]:
                    error_message = response_data["error"]
                # 对于message字段，只有在它不是表示成功的消息时才视为错误
                elif (
                    "message" in response_data
                    and response_data["message"]
                    and response_data["message"].lower()
                    not in ["successful", "success", "ok"]
                ):
                    error_message = response_data["message"]
            else:
                # 如果明确是成功响应，记录一下
                logger.warning("API响应成功")
                # 如果有消息字段但不是错误，记录为信息
                if "message" in response_data and response_data["message"]:
                    logger.debug(f"API返回成功消息: {response_data['message']}")

            if error_message:
                logger.error(f"API返回错误消息: {error_message}")
                return ToolResult(error=f"查询失败: {error_message}")

            # 嵌套递归查找mainOrders
            main_orders = self._find_main_orders(response_data, order_no)

            if not main_orders:
                logger.error("找不到订单数据")
                return ToolResult(error=f"未找到订单 {order_no} 的数据")

            # 获取订单数据
            order = main_orders[0] if isinstance(main_orders, list) else main_orders
            logger.debug(f"订单数据字段列表: {list(order.keys())}")

            # 处理订单主信息 - 可能在mainOrderInfo或当前级别
            main_order_info = {}
            if "mainOrderInfo" in order and isinstance(order["mainOrderInfo"], dict):
                main_order_info = order["mainOrderInfo"]
                logger.debug("从mainOrderInfo字段提取订单主信息")
            else:
                main_order_info = order
                logger.debug("使用当前级别数据作为订单主信息")

            # 记录主订单信息字段
            if isinstance(main_order_info, dict):
                logger.debug(f"主订单信息字段: {list(main_order_info.keys())}")

            # 格式化输出
            order_info = []
            # 尝试从不同位置获取订单号
            order_no_value = (
                main_order_info.get("orderNo") or order.get("orderNo") or order_no
            )
            order_info.append(f"订单号: {order_no_value}")

            # 获取状态 - 可能在不同位置
            status_code = -1
            if "status" in main_order_info:
                status_code = main_order_info.get("state")
            elif "status" in order:
                status_code = order.get("status")

            order_info.append(f"状态: {main_order_info.get('stateDesc')}")

            # 获取创建时间
            created_at = (
                main_order_info.get("createTime") or order.get("createTime") or "N/A"
            )
            # 尝试格式化时间戳
            if created_at != "N/A":
                try:
                    created_at = self._format_timestamp(created_at)
                    logger.debug(f"成功格式化创建时间: {created_at}")
                except Exception as e:
                    logger.warning(f"格式化时间戳失败: {str(e)}")
            order_info.append(f"创建时间: {created_at}")

            # 添加支付信息 - 考虑不同的嵌套结构
            payment = None
            if "paymentInfo" in order and order["paymentInfo"]:
                payment = order["paymentInfo"]
                logger.debug("从paymentInfo字段提取支付信息")
            elif "payment" in order and order["payment"]:
                payment = order["payment"]
                logger.debug("从payment字段提取支付信息")
            elif "paymentInfo" in main_order_info and main_order_info["paymentInfo"]:
                payment = main_order_info["paymentInfo"]
                logger.debug("从mainOrderInfo.paymentInfo字段提取支付信息")

            if payment:
                logger.debug(f"支付信息字段: {list(payment.keys())}")
                pay_way = payment.get("payWay", "N/A")
                if pay_way != "N/A":  # 只有当值不是N/A时才添加
                    order_info.append(f"支付方式: {pay_way}")

                pay_status = self._get_payment_status(payment.get("payStatus", -1))
                if (
                    pay_status != "银行端处理中" and pay_status != f"未知状态(-1)"
                ):  # 排除银行端处理中状态
                    order_info.append(f"支付状态: {pay_status}")

                order_info.append(f"支付金额: ¥{payment.get('realPay', 0) / 100:.2f}")

            # 添加商品信息 - 考虑不同的嵌套结构
            items = []
            if "orderItems" in order and order["orderItems"]:
                items = order["orderItems"]
                logger.debug("从orderItems字段提取商品信息")
            elif "items" in order and order["items"]:
                items = order["items"]
                logger.debug("从items字段提取商品信息")
            elif "itemInfo" in order and isinstance(order["itemInfo"], dict):
                # 检查itemInfo下的可能字段
                for field in ["orderItems", "items", "list"]:
                    if field in order["itemInfo"] and order["itemInfo"][field]:
                        items = order["itemInfo"][field]
                        logger.debug(f"从itemInfo.{field}字段提取商品信息")
                        break

            if items:
                if isinstance(items, list) and items:
                    logger.debug(
                        f"商品信息第一项字段: {list(items[0].keys()) if isinstance(items[0], dict) else 'not a dict'}"
                    )
                order_info.append("\n商品信息:")
                for idx, item in enumerate(items, 1):
                    # 提取商品标题，尝试多个可能的字段名
                    title = item.get("title", "N/A")
                    if not title or title == "N/A":
                        title = item.get("itemName", item.get("productName", "N/A"))

                    # 提取商品ID信息
                    item_id = item.get("itemId", item.get("productId", "N/A"))
                    order_info.append(f"  {idx}. {title} [ID: {item_id}]")

                    # 提取SKU信息
                    sku_id = item.get("skuId", item.get("sku_id", "N/A"))
                    if sku_id != "N/A":
                        order_info.append(f"     SKU ID: {sku_id}")

                    # 尝试提取规格信息
                    sku_properties = item.get(
                        "skuProperties", item.get("sku_properties", "")
                    )
                    if sku_properties:
                        if isinstance(sku_properties, list):
                            props = []
                            for prop in sku_properties:
                                if isinstance(prop, dict):
                                    k = prop.get("k", prop.get("name", ""))
                                    v = prop.get("v", prop.get("value", ""))
                                    if k and v:
                                        props.append(f"{k}: {v}")
                            if props:
                                order_info.append(f"     规格: {'; '.join(props)}")
                        elif isinstance(sku_properties, str):
                            order_info.append(f"     规格: {sku_properties}")

                    # 尝试不同的价格字段名称
                    price = 0
                    for price_field in [
                        "price",
                        "unitPrice",
                        "itemPrice",
                        "realUnitPrice",
                    ]:
                        if price_field in item and item[price_field]:
                            price = item[price_field]
                            break
                    order_info.append(f"     单价: ¥{price / 100:.2f}")

                    # 尝试不同的数量字段名称
                    num = 0
                    for num_field in ["num", "quantity", "itemNum", "count"]:
                        if num_field in item and item[num_field]:
                            num = item[num_field]
                            break
                    order_info.append(f"     数量: {num}")

                    # 计算总价或获取总价字段
                    total_price = 0
                    for total_field in [
                        "totalPrice",
                        "totalFee",
                        "payment",
                        "realTotalPrice",
                    ]:
                        if total_field in item and item[total_field]:
                            total_price = item[total_field]
                            break
                    if total_price == 0 and price > 0 and num > 0:
                        total_price = price * num
                    order_info.append(f"     总价: ¥{total_price / 100:.2f}")

            # 添加买家信息
            buyer = None
            if "buyerInfo" in order and order["buyerInfo"]:
                buyer = order["buyerInfo"]
                logger.debug("从buyerInfo字段提取买家信息")
            elif "buyer" in order and order["buyer"]:
                buyer = order["buyer"]
                logger.debug("从buyer字段提取买家信息")

            if buyer:
                logger.debug(f"买家信息字段: {list(buyer.keys())}")
                order_info.append("\n买家信息:")

                # 买家ID
                buyer_id = (
                    buyer.get("buyerId")
                    or buyer.get("yzUid")
                    or buyer.get("uid")
                    or buyer.get("id")
                    or "N/A"
                )
                order_info.append(f"  买家ID: {buyer_id}")

                # 买家名称 - 只在非N/A时添加
                buyer_name = (
                    buyer.get("buyerName")
                    or buyer.get("nickname")
                    or buyer.get("name")
                    or buyer.get("userName")
                    or "N/A"
                )
                if buyer_name != "N/A":
                    order_info.append(f"  买家名: {buyer_name}")

                # 电话号码(带隐私保护)
                if "mobile" in buyer and buyer["mobile"]:
                    mobile = buyer["mobile"]
                    # 隐私保护: 133****8899
                    if len(mobile) >= 11:
                        protected_mobile = f"{mobile[:3]}****{mobile[-4:]}"
                        order_info.append(f"  联系电话: {protected_mobile}")
                    else:
                        order_info.append(f"  联系电话: {mobile}")

                # 备选电话字段
                elif "phone" in buyer and buyer["phone"]:
                    phone = buyer["phone"]
                    if len(phone) >= 11:
                        protected_phone = f"{phone[:3]}****{phone[-4:]}"
                        order_info.append(f"  联系电话: {protected_phone}")
                    else:
                        order_info.append(f"  联系电话: {phone}")

                # 粉丝类型
                if "fans_type" in buyer and buyer["fans_type"]:
                    order_info.append(f"  粉丝类型: {buyer['fans_type']}")
                elif "fansType" in buyer and buyer["fansType"]:
                    order_info.append(f"  粉丝类型: {buyer['fansType']}")

                # 会员等级
                if "level" in buyer and buyer["level"]:
                    order_info.append(f"  会员等级: {buyer['level']}")
                elif "memberLevel" in buyer and buyer["memberLevel"]:
                    order_info.append(f"  会员等级: {buyer['memberLevel']}")

                # 用户来源
                if "source" in buyer and buyer["source"]:
                    order_info.append(f"  用户来源: {buyer['source']}")
                elif "channel" in buyer and buyer["channel"]:
                    order_info.append(f"  用户来源: {buyer['channel']}")

                # 注册时间
                if "created_at" in buyer and buyer["created_at"]:
                    try:
                        reg_time = self._format_timestamp(buyer["created_at"])
                        order_info.append(f"  注册时间: {reg_time}")
                    except:
                        order_info.append(f"  注册时间: {buyer['created_at']}")
                elif "createTime" in buyer and buyer["createTime"]:
                    try:
                        reg_time = self._format_timestamp(buyer["createTime"])
                        order_info.append(f"  注册时间: {reg_time}")
                    except:
                        order_info.append(f"  注册时间: {buyer['createTime']}")

            # 添加备注信息 - 可能在不同位置
            remark = ""
            if "remark" in order and order["remark"]:
                remark = order["remark"]
            elif "remarkInfo" in order and isinstance(order["remarkInfo"], dict):
                if "buyerMessage" in order["remarkInfo"]:
                    remark = order["remarkInfo"]["buyerMessage"]
                elif "remark" in order["remarkInfo"]:
                    remark = order["remarkInfo"]["remark"]

            if remark:
                order_info.append(f"\n备注: {remark}")

            return ToolResult(output="\n".join(order_info))
        except Exception as e:
            logger.error(f"处理订单响应数据错误: {str(e)}", exc_info=True)
            return ToolResult(error=f"处理订单数据出错: {str(e)}")

    def _find_main_orders(self, data, order_no, path=""):
        """递归查找订单数据，适应不同的嵌套结构"""
        current_path = path

        # 开始检查前记录当前要搜索的路径
        if not path:
            logger.debug(f"开始在数据中查找订单{order_no}")

        # 直接路径
        if "mainOrders" in data:
            logger.debug(f"在路径 {current_path}.mainOrders 找到订单数据")
            return data["mainOrders"]

        # 检查data字段
        if "data" in data:
            logger.debug(f"检查 {current_path}.data 路径")
            if isinstance(data["data"], dict):
                # data字段下的mainOrders
                if "mainOrders" in data["data"]:
                    logger.debug(f"在路径 {current_path}.data.mainOrders 找到订单数据")
                    return data["data"]["mainOrders"]

                # data下可能有order或orders字段
                if "order" in data["data"]:
                    logger.debug(f"在路径 {current_path}.data.order 找到订单数据")
                    return data["data"]["order"]

                if "orders" in data["data"]:
                    if isinstance(data["data"]["orders"], list):
                        logger.debug(f"在路径 {current_path}.data.orders 找到订单列表")
                        # 可能需要匹配订单号
                        for order in data["data"]["orders"]:
                            if order.get("orderNo") == order_no:
                                logger.debug(
                                    f"在路径 {current_path}.data.orders 找到匹配的订单 {order_no}"
                                )
                                return [order]
                        # 如果没找到匹配的但有订单，返回第一个
                        if data["data"]["orders"]:
                            logger.debug(
                                f"在路径 {current_path}.data.orders 没有找到匹配订单号的订单，返回第一个"
                            )
                            return data["data"]["orders"]
                    elif isinstance(data["data"]["orders"], dict):
                        logger.debug(
                            f"在路径 {current_path}.data.orders 找到订单数据(字典类型)"
                        )
                        return data["data"]["orders"]

                # 递归检查所有data下的字段
                for key, value in data["data"].items():
                    if isinstance(value, (dict, list)):
                        logger.debug(f"递归检查 {current_path}.data.{key}")
                        result = self._find_main_orders(
                            value, order_no, f"{current_path}.data.{key}"
                        )
                        if result:
                            return result

            # data字段可能直接是列表
            elif isinstance(data["data"], list) and data["data"]:
                logger.debug(f"在路径 {current_path}.data 发现列表数据")
                # 检查第一个元素
                return data["data"]

        # 检查其他可能的顶级路径
        for top_field in ["result", "response", "orderData", "content"]:
            if top_field in data and data[top_field]:
                logger.debug(f"检查 {current_path}.{top_field} 路径")
                if isinstance(data[top_field], dict):
                    # 递归检查该字段
                    result = self._find_main_orders(
                        data[top_field], order_no, f"{current_path}.{top_field}"
                    )
                    if result:
                        return result
                elif isinstance(data[top_field], list) and data[top_field]:
                    # 如果是列表且有内容，返回该列表
                    logger.debug(f"在路径 {current_path}.{top_field} 找到列表数据")
                    return data[top_field]

        # 直接检查顶层是否有订单信息
        for key in ["order", "orders", "list", "items"]:
            if key in data:
                if isinstance(data[key], dict):
                    logger.debug(f"在路径 {current_path}.{key} 找到订单数据(字典)")
                    return data[key]
                elif isinstance(data[key], list) and data[key]:
                    logger.debug(f"在路径 {current_path}.{key} 找到订单列表")
                    return data[key]

        # 如果到这里还没找到，直接打印当前探索的数据结构
        if not path:  # 只在顶层记录，避免递归时重复记录
            try:
                # 记录数据结构以便调试
                logger.debug(
                    f"没有找到标准订单数据结构，数据顶层键: {list(data.keys())}"
                )
                if "data" in data and data["data"]:
                    if isinstance(data["data"], dict):
                        logger.debug(f"data字段内的键: {list(data['data'].keys())}")
                    elif isinstance(data["data"], list):
                        logger.debug(f"data字段是列表，长度: {len(data['data'])}")
                        if data["data"]:
                            first_item = data["data"][0]
                            if isinstance(first_item, dict):
                                logger.debug(
                                    f"data列表第一项的键: {list(first_item.keys())}"
                                )

                # 作为最后尝试，如果有data字段且不为空，直接返回data
                if "data" in data and data["data"]:
                    logger.debug("作为最后尝试，直接返回data字段")
                    return data["data"]
            except Exception as e:
                logger.error(f"记录数据结构时出错: {str(e)}")

        return None

    def _get_order_status(self, status_code: int) -> str:
        """将订单状态码转换为文字描述"""
        status_map = {
            1: "待付款",
            2: "待发货",
            3: "待收货",
            4: "已完成",
            5: "已关闭",
            6: "退款中",
            7: "已退款",
            8: "维权中",
            # 可以根据需要添加更多状态
        }
        return status_map.get(status_code, f"未知状态({status_code})")

    def _get_payment_status(self, status_code: int) -> str:
        """将支付状态码转换为文字描述"""
        status_map = {
            -1: "银行端处理中",
            0: "未知状态",
            1: "未支付",
            2: "已支付",
            3: "已退款",
            4: "部分退款",
            5: "支付失败",
            6: "取消支付",
            7: "支付超时",
            8: "待确认",
            9: "处理中",
            10: "支付中断",
            # 可以根据需要添加更多状态
        }
        return status_map.get(status_code, f"未知状态({status_code})")

    def _format_timestamp(self, timestamp):
        """将时间戳转换为可读的日期时间格式"""
        try:
            # 有赞API返回的时间戳通常是毫秒级的
            if isinstance(timestamp, str) and timestamp.isdigit():
                timestamp = int(timestamp)

            if isinstance(timestamp, int) and timestamp > 1000000000000:  # 毫秒级时间戳
                timestamp = timestamp / 1000

            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"转换时间戳失败: {str(e)}")
            return str(timestamp)  # 返回原始时间戳作为字符串
