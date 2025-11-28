"""
Backtesting Visualization.

Chart generation utilities for backtest results.
"""

from maverick_backtest.visualization.charts import (
    generate_equity_curve,
    generate_optimization_heatmap,
    generate_performance_dashboard,
    generate_portfolio_allocation,
    generate_returns_distribution,
    generate_rolling_metrics,
    generate_strategy_comparison,
    generate_trade_scatter,
    image_to_base64,
    set_chart_style,
)

__all__ = [
    "set_chart_style",
    "image_to_base64",
    "generate_equity_curve",
    "generate_trade_scatter",
    "generate_optimization_heatmap",
    "generate_portfolio_allocation",
    "generate_strategy_comparison",
    "generate_performance_dashboard",
    "generate_returns_distribution",
    "generate_rolling_metrics",
]
