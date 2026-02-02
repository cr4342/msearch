"""
相关性反馈处理
处理用户对搜索结果的反馈，用于改进搜索质量
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RelevanceFeedback:
    """相关性反馈处理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化相关性反馈处理器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.feedback_store = {}

    async def record_feedback(
        self,
        query_id: str,
        result_id: str,
        user_feedback: int,
        feedback_type: str = "explicit",
    ) -> bool:
        """
        记录用户反馈

        Args:
            query_id: 查询ID
            result_id: 结果ID
            user_feedback: 用户反馈 (-1: 不相关, 0: 中性, 1: 相关)
            feedback_type: 反馈类型 (explicit/implicit)

        Returns:
            是否成功
        """
        feedback_entry = {
            "query_id": query_id,
            "result_id": result_id,
            "user_feedback": user_feedback,
            "feedback_type": feedback_type,
            "timestamp": datetime.now().isoformat(),
        }

        if query_id not in self.feedback_store:
            self.feedback_store[query_id] = []

        self.feedback_store[query_id].append(feedback_entry)

        logger.info(
            f"记录反馈: query={query_id}, result={result_id}, feedback={user_feedback}"
        )
        return True

    async def get_feedback_for_query(self, query_id: str) -> List[Dict[str, Any]]:
        """
        获取查询的反馈记录

        Args:
            query_id: 查询ID

        Returns:
            反馈记录列表
        """
        return self.feedback_store.get(query_id, [])

    async def calculate_relevance_scores(
        self, query_id: str, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        计算基于反馈的相关性分数

        Args:
            query_id: 查询ID
            results: 原始结果列表

        Returns:
            调整后的结果列表
        """
        feedback_list = await self.get_feedback_for_query(query_id)

        if not feedback_list:
            return results

        result_scores = {r.get("id", r.get("file_id", "")): 0.0 for r in results}

        for feedback in feedback_list:
            result_id = feedback["result_id"]
            user_feedback = feedback["user_feedback"]
            if result_id in result_scores:
                result_scores[result_id] += user_feedback * 0.3

        adjusted_results = []
        for result in results:
            result_id = result.get("id", result.get("file_id", ""))
            if result_id in result_scores:
                original_score = result.get("relevance_score", result.get("score", 0.0))
                adjusted_score = original_score + result_scores[result_id]
                result["relevance_score"] = max(0.0, min(1.0, adjusted_score))
                adjusted_results.append(result)

        adjusted_results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)

        return adjusted_results

    async def clear_feedback(self, query_id: Optional[str] = None) -> bool:
        """
        清除反馈记录

        Args:
            query_id: 查询ID，None表示清除所有

        Returns:
            是否成功
        """
        if query_id:
            if query_id in self.feedback_store:
                del self.feedback_store[query_id]
        else:
            self.feedback_store.clear()

        return True
