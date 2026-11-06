# -*- coding: utf-8 -*-
"""
第四周 · AgentScope 状态机 + 多轮对话
基于 AgentScope 2.0 实现价格分析 Agent 的状态机：
    状态流转：待命(IDLE) -> 意图识别(INTENT) -> 调工具(EXECUTE) -> 追问补齐(ASK) -> 返回(RESPOND)

职责划分（任务书硬约束）：
  - LLM（DeepSeek）只负责意图识别、多轮追问、结果文本整理
  - 所有价格/预测/告警数据必须通过工具调用后端接口读取，禁止 LLM 直接编造

状态机（State）：
  IDLE     待命：等待用户输入
  INTENT   识别意图：调用 DeepSeek 解析自然语言
  EXECUTE  执行：根据意图调用对应工具（查价/预测/告警/阈值）
  ASK      追问：信息不全时反问用户补齐（如商品名缺失）
  RESPOND  返回：整理结果，生成自然语言回答
"""
import json

from agentscope.agent import Agent
from agentscope.credential import OpenAICredential
from agentscope.model import OpenAIChatModel
from agentscope.tool import FunctionTool, Toolkit
from agentscope.message import UserMsg

import config
import intent as intent_module
import tools


# ========== 状态定义 ==========
class State:
    IDLE = "IDLE"
    INTENT = "INTENT"
    EXECUTE = "EXECUTE"
    ASK = "ASK"
    RESPOND = "RESPOND"


# ========== Agent 实例（基于 AgentScope 2.0） ==========
def _build_agent():
    """构建 AgentScope Agent，注册价格分析工具"""
    # DeepSeek 通过 OpenAI 兼容接口接入
    credential = OpenAICredential(
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
    )
    model = OpenAIChatModel(
        credential=credential,
        model=config.DEEPSEEK_MODEL,
        stream=False,
    )
    # 把 tools.py 里的函数包装成工具，注册进 Toolkit
    toolkit = Toolkit(tools=[
        FunctionTool(
            tools.query_price,
            name="query_price",
            description="查询某商品最近N天的历史价格，参数 goods_id(商品ID) 和 days(天数)，返回价格列表",
        ),
        FunctionTool(
            tools.query_forecast,
            name="query_forecast",
            description="查询某商品未来7天的价格预测，参数 goods_id(商品ID)，返回预测列表",
        ),
        FunctionTool(
            tools.query_alerts,
            name="query_alerts",
            description="查询价格告警记录，参数 goods_id(可选)，返回告警列表",
        ),
        FunctionTool(
            tools.get_threshold,
            name="get_threshold",
            description="查询某商品的告警阈值配置，参数 goods_id(可选)，返回阈值配置",
        ),
        FunctionTool(
            tools.set_threshold,
            name="set_threshold",
            description="设置某商品的告警阈值，参数 goods_id、up_threshold、down_threshold",
        ),
    ])
    agent = Agent(
        name="价格分析助手",
        system_prompt=(
            "你是商品价格预测系统的智能助手。"
            "你只能通过调用工具（query_price/query_forecast/query_alerts 等）获取真实数据，"
            "禁止编造任何价格、预测或告警数据。"
            "当用户问价格走势时，用工具查真实数据后，用通俗语言解读。"
        ),
        model=model,
        toolkit=toolkit,
    )
    return agent


# ========== 状态机主类 ==========
class PriceAgentStateMachine:
    def __init__(self):
        self.agent = _build_agent()
        self.state = State.IDLE
        self.context = {}       # 多轮对话上下文（记住上一轮的意图和商品）
        self.history = []       # 对话历史（用于多轮指代消解）

    def _build_goods_names(self):
        """从后端动态查"期货农产品"分类的商品名列表（用于追问时列出可选商品）"""
        return intent_module.list_goods_names()

    def handle(self, user_text):
        """
        处理一条用户输入，返回 (回复文本, 状态)
        """
        # 1. 状态：IDLE -> INTENT
        self.state = State.INTENT

        # 2. 意图识别（DeepSeek）
        try:
            parsed = intent_module.recognize_intent(user_text)
        except Exception as e:
            return f"[意图识别失败] {e}", State.IDLE

        intent_type = parsed.get("intent_type", "chat")
        goods_name = parsed.get("goods_name")
        days = parsed.get("days")

        # 多轮指代消解：如果没提商品，但上下文里有，就用上文的
        if not goods_name and self.context.get("goods_name"):
            goods_name = self.context["goods_name"]

        # 3. 状态：根据意图分支
        if intent_type == "chat":
            # 闲聊，直接让 Agent 回复
            self.state = State.RESPOND
            reply = self._agent_chat(user_text)
            return reply, self.state

        # 需要商品的意图：商品名缺失 -> 追问
        if intent_type in ("price_query", "forecast", "threshold") and not goods_name:
            self.state = State.ASK
            reply = self._ask_goods(intent_type)
            return reply, self.state

        # 4. 状态：EXECUTE（调用工具，_execute 内部已格式化结果文本）
        self.state = State.EXECUTE
        reply = self._execute(intent_type, goods_name, days)

        # 5. 状态：RESPOND（返回结果）
        self.state = State.RESPOND

        # 6. 更新上下文（多轮记忆）
        if goods_name:
            self.context["goods_name"] = goods_name
        self.context["last_intent"] = intent_type

        return reply, self.state

    def _execute(self, intent_type, goods_name, days):
        """根据意图调用对应工具，返回结构化结果文本"""
        goods_id = intent_module.resolve_goods_id(goods_name)

        if intent_type == "price_query":
            if goods_id is None:
                return f"未识别到商品「{goods_name}」，请确认商品名"
            d = days or 30
            data = tools.query_price(goods_id, days=d)
            return self._format_price(data)

        if intent_type == "forecast":
            if goods_id is None:
                return f"未识别到商品「{goods_name}」，请确认商品名"
            data = tools.query_forecast(goods_id)
            return self._format_forecast(data)

        if intent_type == "alert_query":
            data = tools.query_alerts()
            return self._format_alerts(data)

        if intent_type == "threshold":
            data = tools.get_threshold()
            return self._format_threshold(data)

        return "无法处理该意图"

    def _agent_chat(self, user_text):
        """闲聊：直接用 AgentScope Agent 回复"""
        try:
            msg = UserMsg(name="user", content=user_text)
            reply = self.agent.reply(msg)
            # 提取文本内容
            return str(reply.get_text_content())
        except Exception as e:
            return f"[回复失败] {e}"

    def _ask_goods(self, intent_type):
        """追问：信息不全时反问用户指定商品"""
        names = "、".join(self._build_goods_names())
        action_map = {
            "price_query": "查询价格",
            "forecast": "预测价格",
            "threshold": "配置告警阈值",
        }
        action = action_map.get(intent_type, "操作")
        return f"请问您想{action}哪个商品？目前支持：{names}。例如「查猪肉最近30天价格」"

    # ===== 格式化工具结果 =====
    def _format_price(self, data):
        if not data:
            return "该商品暂无价格数据"
        lines = [f"共 {len(data)} 条价格记录："]
        for p in data[:10]:
            lines.append(f"  {p.get('priceDate')}  {p.get('price')} {p.get('priceUnit', '')}")
        if len(data) > 10:
            lines.append(f"  ...（共 {len(data)} 条）")
        return "\n".join(lines)

    def _format_forecast(self, data):
        if not data:
            return "该商品暂无预测数据"
        lines = ["未来 7 天价格预测："]
        for f in data:
            lines.append(f"  {f.get('forecastDate')}  预测价 {f.get('forecastPrice')}")
        return "\n".join(lines)

    def _format_alerts(self, data):
        if not data:
            return "暂无价格告警记录"
        lines = [f"共 {len(data)} 条告警："]
        for a in data[:10]:
            lines.append(
                f"  商品ID={a.get('goodsId')}  {a.get('alertType')} 变化率 {a.get('changeRate')}% "
                f"状态 {a.get('alertStatus')}"
            )
        return "\n".join(lines)

    def _format_threshold(self, data):
        if not data:
            return "暂无阈值配置"
        if isinstance(data, list):
            lines = ["当前告警阈值配置："]
            for t in data:
                lines.append(f"  商品ID={t.get('goodsId')}  上涨 {t.get('upThreshold')}%  下跌 {t.get('downThreshold')}%")
            return "\n".join(lines)
        return f"商品ID={data.get('goodsId')}  上涨 {data.get('upThreshold')}%  下跌 {data.get('downThreshold')}%"


if __name__ == "__main__":
    # 自测
    sm = PriceAgentStateMachine()
    tests = [
        "查猪肉最近30天价格",
        "预测鲜苹果未来7天价格",
        "看看最近有没有价格告警",
    ]
    for t in tests:
        reply, state = sm.handle(t)
        print(f"\n{'='*50}")
        print(f"用户: {t}")
        print(f"状态: {state}")
        print(f"回复:\n{reply}")
