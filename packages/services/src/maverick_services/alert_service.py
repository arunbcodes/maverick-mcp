"""
AI Alert Service.

Monitors screening criteria and generates alerts when new opportunities appear.
Supports configurable alert rules with real-time notifications via SSE.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from enum import Enum
from typing import AsyncIterator
from uuid import uuid4

from redis.asyncio import Redis

from maverick_core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
# ============================================
# Enums and Data Classes
# ============================================


class AlertType(Enum):
    """Types of alerts."""
    
    # Screening alerts
    NEW_MAVERICK_STOCK = "new_maverick_stock"
    NEW_BEAR_STOCK = "new_bear_stock"
    NEW_BREAKOUT = "new_breakout"
    
    # Technical alerts
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"
    PRICE_BREAKOUT = "price_breakout"
    VOLUME_SPIKE = "volume_spike"
    
    # Portfolio alerts
    POSITION_GAIN = "position_gain"
    POSITION_LOSS = "position_loss"
    STOP_LOSS_HIT = "stop_loss_hit"
    PRICE_TARGET_HIT = "price_target_hit"
    
    # Risk alerts (Phase 7E)
    HIGH_CORRELATION = "high_correlation"  # Holdings become highly correlated
    LOW_DIVERSIFICATION = "low_diversification"  # Score drops below threshold
    CONCENTRATION_WARNING = "concentration_warning"  # Position exceeds threshold
    SECTOR_DRIFT = "sector_drift"  # Sector allocation drifts from target
    VAR_BREACH = "var_breach"  # VaR exceeds threshold
    BETA_HIGH = "beta_high"  # Portfolio beta exceeds threshold


class AlertPriority(Enum):
    """Alert priority levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"
    ACTED_ON = "acted_on"


@dataclass
class AlertRule:
    """Configuration for an alert rule."""
    
    rule_id: str
    user_id: str
    name: str
    alert_type: AlertType
    enabled: bool = True
    
    # Conditions
    conditions: dict = field(default_factory=dict)
    # Examples:
    # - {"min_score": 80} for maverick alerts
    # - {"threshold": 30, "direction": "below"} for RSI
    # - {"ticker": "AAPL", "target_price": 200} for price alerts
    # - {"percent_change": 10} for position gain/loss
    
    # Notification settings
    priority: AlertPriority = AlertPriority.MEDIUM
    notify_email: bool = False
    notify_push: bool = True
    
    # Cooldown (prevent spam)
    cooldown_minutes: int = 60
    last_triggered: datetime | None = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


@dataclass
class Alert:
    """A triggered alert."""
    
    alert_id: str
    user_id: str
    rule_id: str | None
    alert_type: AlertType
    priority: AlertPriority
    
    # Content
    title: str
    message: str
    ticker: str | None = None
    data: dict = field(default_factory=dict)
    
    # AI-generated insight
    ai_insight: str | None = None
    
    # Status
    status: AlertStatus = AlertStatus.UNREAD
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    read_at: datetime | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "alert_id": self.alert_id,
            "user_id": self.user_id,
            "rule_id": self.rule_id,
            "alert_type": self.alert_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "ticker": self.ticker,
            "data": self.data,
            "ai_insight": self.ai_insight,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        """Create from dictionary."""
        return cls(
            alert_id=data["alert_id"],
            user_id=data["user_id"],
            rule_id=data.get("rule_id"),
            alert_type=AlertType(data["alert_type"]),
            priority=AlertPriority(data["priority"]),
            title=data["title"],
            message=data["message"],
            ticker=data.get("ticker"),
            data=data.get("data", {}),
            ai_insight=data.get("ai_insight"),
            status=AlertStatus(data.get("status", "unread")),
            created_at=datetime.fromisoformat(data["created_at"]),
            read_at=datetime.fromisoformat(data["read_at"]) if data.get("read_at") else None,
        )


# ============================================
# Alert Service
# ============================================


class AlertService:
    """
    Service for managing AI-powered alerts.
    
    Features:
    - Configurable alert rules per user
    - Real-time monitoring via background tasks
    - SSE streaming for instant notifications
    - AI-generated insights for each alert
    - Rate limiting and cooldowns
    """
    
    # Redis keys
    RULES_KEY = "alerts:rules:{user_id}"
    ALERTS_KEY = "alerts:history:{user_id}"
    STREAM_KEY = "alerts:stream:{user_id}"
    COOLDOWN_KEY = "alerts:cooldown:{rule_id}"
    UNREAD_COUNT_KEY = "alerts:unread:{user_id}"
    
    # Limits
    MAX_RULES_PER_USER = 20
    MAX_ALERTS_HISTORY = 100
    ALERT_TTL_DAYS = 30
    
    def __init__(
        self,
        redis_client: Redis | None = None,
        llm_api_key: str | None = None,
    ):
        self.redis = redis_client
        self.llm_api_key = llm_api_key
        self._monitoring_tasks: dict[str, asyncio.Task] = {}
    
    # ================================
    # Rule Management
    # ================================
    
    async def create_rule(
        self,
        user_id: str,
        name: str,
        alert_type: AlertType,
        conditions: dict,
        priority: AlertPriority = AlertPriority.MEDIUM,
        cooldown_minutes: int = 60,
    ) -> AlertRule:
        """Create a new alert rule."""
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        # Check rule limit
        existing_rules = await self.get_rules(user_id)
        if len(existing_rules) >= self.MAX_RULES_PER_USER:
            raise ValueError(f"Maximum {self.MAX_RULES_PER_USER} rules allowed")
        
        rule = AlertRule(
            rule_id=str(uuid4()),
            user_id=user_id,
            name=name,
            alert_type=alert_type,
            conditions=conditions,
            priority=priority,
            cooldown_minutes=cooldown_minutes,
        )
        
        # Store rule
        rules_key = self.RULES_KEY.format(user_id=user_id)
        await self.redis.hset(
            rules_key,
            rule.rule_id,
            json.dumps(self._rule_to_dict(rule)),
        )
        
        logger.info(f"Created alert rule {rule.rule_id} for user {user_id}")
        return rule
    
    async def get_rules(self, user_id: str) -> list[AlertRule]:
        """Get all rules for a user."""
        if not self.redis:
            return []
        
        rules_key = self.RULES_KEY.format(user_id=user_id)
        rules_data = await self.redis.hgetall(rules_key)
        
        rules = []
        for rule_json in rules_data.values():
            try:
                rule_dict = json.loads(rule_json)
                rules.append(self._rule_from_dict(rule_dict))
            except Exception as e:
                logger.warning(f"Failed to parse rule: {e}")
        
        return rules
    
    async def get_rule(self, user_id: str, rule_id: str) -> AlertRule | None:
        """Get a specific rule."""
        if not self.redis:
            return None
        
        rules_key = self.RULES_KEY.format(user_id=user_id)
        rule_json = await self.redis.hget(rules_key, rule_id)
        
        if not rule_json:
            return None
        
        return self._rule_from_dict(json.loads(rule_json))
    
    async def update_rule(
        self,
        user_id: str,
        rule_id: str,
        updates: dict,
    ) -> AlertRule | None:
        """Update a rule."""
        if not self.redis:
            return None
        
        rule = await self.get_rule(user_id, rule_id)
        if not rule:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.now(UTC)
        
        # Save
        rules_key = self.RULES_KEY.format(user_id=user_id)
        await self.redis.hset(
            rules_key,
            rule_id,
            json.dumps(self._rule_to_dict(rule)),
        )
        
        return rule
    
    async def delete_rule(self, user_id: str, rule_id: str) -> bool:
        """Delete a rule."""
        if not self.redis:
            return False
        
        rules_key = self.RULES_KEY.format(user_id=user_id)
        deleted = await self.redis.hdel(rules_key, rule_id)
        return deleted > 0
    
    async def toggle_rule(self, user_id: str, rule_id: str, enabled: bool) -> bool:
        """Enable or disable a rule."""
        rule = await self.update_rule(user_id, rule_id, {"enabled": enabled})
        return rule is not None
    
    # ================================
    # Alert Triggering
    # ================================
    
    async def trigger_alert(
        self,
        user_id: str,
        alert_type: AlertType,
        title: str,
        message: str,
        ticker: str | None = None,
        data: dict | None = None,
        rule_id: str | None = None,
        priority: AlertPriority = AlertPriority.MEDIUM,
        generate_insight: bool = True,
    ) -> Alert:
        """
        Trigger an alert for a user.
        
        This creates the alert, stores it in history, and publishes
        to the SSE stream for real-time delivery.
        """
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        # Check cooldown if rule-based
        if rule_id:
            cooldown_key = self.COOLDOWN_KEY.format(rule_id=rule_id)
            if await self.redis.exists(cooldown_key):
                logger.debug(f"Rule {rule_id} in cooldown, skipping alert")
                raise ValueError("Alert in cooldown period")
        
        # Generate AI insight if enabled
        ai_insight = None
        if generate_insight and ticker:
            ai_insight = await self._generate_alert_insight(
                alert_type=alert_type,
                ticker=ticker,
                data=data or {},
            )
        
        # Create alert
        alert = Alert(
            alert_id=str(uuid4()),
            user_id=user_id,
            rule_id=rule_id,
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            ticker=ticker,
            data=data or {},
            ai_insight=ai_insight,
        )
        
        # Store in history
        alerts_key = self.ALERTS_KEY.format(user_id=user_id)
        await self.redis.lpush(alerts_key, json.dumps(alert.to_dict()))
        await self.redis.ltrim(alerts_key, 0, self.MAX_ALERTS_HISTORY - 1)
        await self.redis.expire(alerts_key, self.ALERT_TTL_DAYS * 86400)
        
        # Increment unread count
        unread_key = self.UNREAD_COUNT_KEY.format(user_id=user_id)
        await self.redis.incr(unread_key)
        
        # Publish to SSE stream
        stream_key = self.STREAM_KEY.format(user_id=user_id)
        await self.redis.publish(stream_key, json.dumps(alert.to_dict()))
        
        # Set cooldown if rule-based
        if rule_id:
            rule = await self.get_rule(user_id, rule_id)
            if rule:
                cooldown_key = self.COOLDOWN_KEY.format(rule_id=rule_id)
                await self.redis.setex(
                    cooldown_key,
                    rule.cooldown_minutes * 60,
                    "1",
                )
        
        logger.info(f"Triggered alert {alert.alert_id} for user {user_id}: {title}")
        return alert
    
    # ================================
    # Alert History
    # ================================
    
    async def get_alerts(
        self,
        user_id: str,
        limit: int = 50,
        status: AlertStatus | None = None,
    ) -> list[Alert]:
        """Get alert history for a user."""
        if not self.redis:
            return []
        
        alerts_key = self.ALERTS_KEY.format(user_id=user_id)
        alerts_json = await self.redis.lrange(alerts_key, 0, limit - 1)
        
        alerts = []
        for alert_json in alerts_json:
            try:
                alert = Alert.from_dict(json.loads(alert_json))
                if status is None or alert.status == status:
                    alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to parse alert: {e}")
        
        return alerts
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread alerts."""
        if not self.redis:
            return 0
        
        unread_key = self.UNREAD_COUNT_KEY.format(user_id=user_id)
        count = await self.redis.get(unread_key)
        return int(count) if count else 0
    
    async def mark_as_read(self, user_id: str, alert_id: str) -> bool:
        """Mark an alert as read."""
        if not self.redis:
            return False
        
        alerts_key = self.ALERTS_KEY.format(user_id=user_id)
        alerts_json = await self.redis.lrange(alerts_key, 0, -1)
        
        for i, alert_json in enumerate(alerts_json):
            alert_dict = json.loads(alert_json)
            if alert_dict["alert_id"] == alert_id:
                if alert_dict["status"] == AlertStatus.UNREAD.value:
                    alert_dict["status"] = AlertStatus.READ.value
                    alert_dict["read_at"] = datetime.now(UTC).isoformat()
                    await self.redis.lset(alerts_key, i, json.dumps(alert_dict))
                    
                    # Decrement unread count
                    unread_key = self.UNREAD_COUNT_KEY.format(user_id=user_id)
                    await self.redis.decr(unread_key)
                return True
        
        return False
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all alerts as read. Returns count marked."""
        if not self.redis:
            return 0
        
        alerts_key = self.ALERTS_KEY.format(user_id=user_id)
        alerts_json = await self.redis.lrange(alerts_key, 0, -1)
        
        count = 0
        for i, alert_json in enumerate(alerts_json):
            alert_dict = json.loads(alert_json)
            if alert_dict["status"] == AlertStatus.UNREAD.value:
                alert_dict["status"] = AlertStatus.READ.value
                alert_dict["read_at"] = datetime.now(UTC).isoformat()
                await self.redis.lset(alerts_key, i, json.dumps(alert_dict))
                count += 1
        
        # Reset unread count
        unread_key = self.UNREAD_COUNT_KEY.format(user_id=user_id)
        await self.redis.set(unread_key, 0)
        
        return count
    
    async def dismiss_alert(self, user_id: str, alert_id: str) -> bool:
        """Dismiss an alert."""
        if not self.redis:
            return False
        
        alerts_key = self.ALERTS_KEY.format(user_id=user_id)
        alerts_json = await self.redis.lrange(alerts_key, 0, -1)
        
        for i, alert_json in enumerate(alerts_json):
            alert_dict = json.loads(alert_json)
            if alert_dict["alert_id"] == alert_id:
                alert_dict["status"] = AlertStatus.DISMISSED.value
                await self.redis.lset(alerts_key, i, json.dumps(alert_dict))
                
                # Decrement unread if was unread
                if alert_dict.get("status") == AlertStatus.UNREAD.value:
                    unread_key = self.UNREAD_COUNT_KEY.format(user_id=user_id)
                    await self.redis.decr(unread_key)
                return True
        
        return False
    
    # ================================
    # SSE Streaming
    # ================================
    
    async def subscribe_to_alerts(
        self,
        user_id: str,
    ) -> AsyncIterator[Alert]:
        """
        Subscribe to real-time alerts via Redis pub/sub.
        
        Yields Alert objects as they are triggered.
        """
        if not self.redis:
            return
        
        stream_key = self.STREAM_KEY.format(user_id=user_id)
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(stream_key)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        alert_dict = json.loads(message["data"])
                        yield Alert.from_dict(alert_dict)
                    except Exception as e:
                        logger.warning(f"Failed to parse alert message: {e}")
        finally:
            await pubsub.unsubscribe(stream_key)
            await pubsub.close()
    
    # ================================
    # Screening Monitors
    # ================================
    
    async def check_maverick_alerts(
        self,
        user_id: str,
        current_results: list[dict],
        previous_results: list[dict] | None = None,
    ) -> list[Alert]:
        """
        Check for new Maverick stocks and trigger alerts.
        
        Compares current screening results with previous to find new entries.
        """
        if not previous_results:
            return []
        
        # Get user's rules for maverick alerts
        rules = await self.get_rules(user_id)
        maverick_rules = [
            r for r in rules
            if r.alert_type == AlertType.NEW_MAVERICK_STOCK and r.enabled
        ]
        
        if not maverick_rules:
            return []
        
        # Find new stocks
        previous_tickers = {r["ticker"] for r in previous_results}
        new_stocks = [
            s for s in current_results
            if s["ticker"] not in previous_tickers
        ]
        
        alerts = []
        for stock in new_stocks:
            for rule in maverick_rules:
                # Check conditions
                min_score = rule.conditions.get("min_score", 0)
                if stock.get("score", 0) < min_score:
                    continue
                
                sectors = rule.conditions.get("sectors", [])
                if sectors and stock.get("sector") not in sectors:
                    continue
                
                try:
                    alert = await self.trigger_alert(
                        user_id=user_id,
                        alert_type=AlertType.NEW_MAVERICK_STOCK,
                        title=f"New Maverick Stock: {stock['ticker']}",
                        message=f"{stock.get('name', stock['ticker'])} added to Maverick screen with score {stock.get('score', 'N/A')}",
                        ticker=stock["ticker"],
                        data=stock,
                        rule_id=rule.rule_id,
                        priority=rule.priority,
                    )
                    alerts.append(alert)
                except ValueError:
                    # Cooldown
                    pass
        
        return alerts
    
    async def check_rsi_alerts(
        self,
        user_id: str,
        ticker: str,
        rsi_value: float,
    ) -> Alert | None:
        """Check RSI thresholds and trigger alert if needed."""
        rules = await self.get_rules(user_id)
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            # Check RSI oversold
            if rule.alert_type == AlertType.RSI_OVERSOLD:
                threshold = rule.conditions.get("threshold", 30)
                if rsi_value <= threshold:
                    try:
                        return await self.trigger_alert(
                            user_id=user_id,
                            alert_type=AlertType.RSI_OVERSOLD,
                            title=f"RSI Oversold: {ticker}",
                            message=f"{ticker} RSI dropped to {rsi_value:.1f} (below {threshold})",
                            ticker=ticker,
                            data={"rsi": rsi_value, "threshold": threshold},
                            rule_id=rule.rule_id,
                            priority=rule.priority,
                        )
                    except ValueError:
                        pass
            
            # Check RSI overbought
            elif rule.alert_type == AlertType.RSI_OVERBOUGHT:
                threshold = rule.conditions.get("threshold", 70)
                if rsi_value >= threshold:
                    try:
                        return await self.trigger_alert(
                            user_id=user_id,
                            alert_type=AlertType.RSI_OVERBOUGHT,
                            title=f"RSI Overbought: {ticker}",
                            message=f"{ticker} RSI rose to {rsi_value:.1f} (above {threshold})",
                            ticker=ticker,
                            data={"rsi": rsi_value, "threshold": threshold},
                            rule_id=rule.rule_id,
                            priority=rule.priority,
                        )
                    except ValueError:
                        pass
        
        return None
    
    async def check_price_target_alert(
        self,
        user_id: str,
        ticker: str,
        current_price: float,
    ) -> Alert | None:
        """Check if price target has been hit."""
        rules = await self.get_rules(user_id)
        
        for rule in rules:
            if rule.alert_type != AlertType.PRICE_TARGET_HIT or not rule.enabled:
                continue
            
            if rule.conditions.get("ticker", "").upper() != ticker.upper():
                continue
            
            target_price = rule.conditions.get("target_price")
            direction = rule.conditions.get("direction", "above")
            
            if not target_price:
                continue
            
            hit = (
                (direction == "above" and current_price >= target_price) or
                (direction == "below" and current_price <= target_price)
            )
            
            if hit:
                try:
                    return await self.trigger_alert(
                        user_id=user_id,
                        alert_type=AlertType.PRICE_TARGET_HIT,
                        title=f"Price Target Hit: {ticker}",
                        message=f"{ticker} reached ${current_price:.2f} ({direction} ${target_price:.2f})",
                        ticker=ticker,
                        data={
                            "current_price": current_price,
                            "target_price": target_price,
                            "direction": direction,
                        },
                        rule_id=rule.rule_id,
                        priority=AlertPriority.HIGH,
                    )
                except ValueError:
                    pass
        
        return None
    
    # ================================
    # AI Insight Generation
    # ================================
    
    async def _generate_alert_insight(
        self,
        alert_type: AlertType,
        ticker: str,
        data: dict,
    ) -> str | None:
        """Generate an AI insight for an alert."""
        if not self.llm_api_key:
            return None
        
        try:
            import httpx
            
            # Build prompt based on alert type
            prompt = self._build_insight_prompt(alert_type, ticker, data)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",  # Fast model for alerts
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a financial analyst providing brief, actionable insights. Be concise (1-2 sentences max).",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 100,
                        "temperature": 0.3,
                    },
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Failed to generate alert insight: {e}")
        
        return None
    
    def _build_insight_prompt(
        self,
        alert_type: AlertType,
        ticker: str,
        data: dict,
    ) -> str:
        """Build prompt for AI insight generation."""
        if alert_type == AlertType.NEW_MAVERICK_STOCK:
            score = data.get("score", "N/A")
            return f"{ticker} just appeared on the Maverick screen with score {score}. What's one key thing to know?"
        
        elif alert_type == AlertType.RSI_OVERSOLD:
            rsi = data.get("rsi", 30)
            return f"{ticker} RSI is {rsi:.1f} (oversold). Quick take on what this might mean?"
        
        elif alert_type == AlertType.RSI_OVERBOUGHT:
            rsi = data.get("rsi", 70)
            return f"{ticker} RSI is {rsi:.1f} (overbought). Quick take on what this might mean?"
        
        elif alert_type == AlertType.PRICE_TARGET_HIT:
            target = data.get("target_price")
            current = data.get("current_price")
            return f"{ticker} hit price target ${target}. Current: ${current}. Quick insight?"
        
        else:
            return f"Brief insight for {ticker} alert: {alert_type.value}"
    
    # ================================
    # Helpers
    # ================================
    
    def _rule_to_dict(self, rule: AlertRule) -> dict:
        """Convert rule to dictionary."""
        return {
            "rule_id": rule.rule_id,
            "user_id": rule.user_id,
            "name": rule.name,
            "alert_type": rule.alert_type.value,
            "enabled": rule.enabled,
            "conditions": rule.conditions,
            "priority": rule.priority.value,
            "notify_email": rule.notify_email,
            "notify_push": rule.notify_push,
            "cooldown_minutes": rule.cooldown_minutes,
            "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None,
            "created_at": rule.created_at.isoformat(),
            "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        }
    
    def _rule_from_dict(self, data: dict) -> AlertRule:
        """Create rule from dictionary."""
        return AlertRule(
            rule_id=data["rule_id"],
            user_id=data["user_id"],
            name=data["name"],
            alert_type=AlertType(data["alert_type"]),
            enabled=data.get("enabled", True),
            conditions=data.get("conditions", {}),
            priority=AlertPriority(data.get("priority", "medium")),
            notify_email=data.get("notify_email", False),
            notify_push=data.get("notify_push", True),
            cooldown_minutes=data.get("cooldown_minutes", 60),
            last_triggered=datetime.fromisoformat(data["last_triggered"]) if data.get("last_triggered") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(UTC),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ============================================
# Factory Function
# ============================================


def get_alert_service(
    redis_client: Redis | None = None,
    llm_api_key: str | None = None,
) -> AlertService:
    """Get AlertService instance."""
    import os
    
    if llm_api_key is None:
        if settings.openrouter_api_key:
            return AlertService(
                redis_client=redis_client,
                llm_api_key=settings.openrouter_api_key
            )
        llm_api_key = os.getenv("OPENROUTER_API_KEY")
    
    return AlertService(
        redis_client=redis_client,
        llm_api_key=llm_api_key,
    )


# ============================================
# Preset Alert Rules
# ============================================


PRESET_RULES = [
    {
        "name": "New Maverick Stocks",
        "alert_type": AlertType.NEW_MAVERICK_STOCK,
        "conditions": {"min_score": 70},
        "description": "Alert when new high-scoring stocks appear on the Maverick screen",
    },
    {
        "name": "RSI Oversold Alert",
        "alert_type": AlertType.RSI_OVERSOLD,
        "conditions": {"threshold": 30},
        "description": "Alert when watched stocks become oversold (RSI < 30)",
    },
    {
        "name": "RSI Overbought Alert",
        "alert_type": AlertType.RSI_OVERBOUGHT,
        "conditions": {"threshold": 70},
        "description": "Alert when watched stocks become overbought (RSI > 70)",
    },
    {
        "name": "New Breakout Stocks",
        "alert_type": AlertType.NEW_BREAKOUT,
        "conditions": {"min_score": 60},
        "description": "Alert when new stocks break out from accumulation patterns",
    },
]

