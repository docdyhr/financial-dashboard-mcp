"""Pydantic schemas for Financial Dashboard."""

# Base schemas
# Asset schemas
from backend.schemas.asset import (
    AssetBase,
    AssetCreate,
    AssetMarketData,
    AssetPriceUpdate,
    AssetResponse,
    AssetSearchParams,
    AssetSummary,
    AssetUpdate,
    BulkAssetPriceUpdate,
)
from backend.schemas.base import (
    BaseResponse,
    BaseSchema,
    ErrorResponse,
    HealthCheck,
    PaginatedResponse,
    PaginationParams,
    StatusResponse,
    TimestampMixin,
)

# Portfolio schemas
from backend.schemas.portfolio import (
    AllocationBreakdown,
    DiversificationMetrics,
    PerformanceMetrics,
    PortfolioAnalyticsResponse,
    PortfolioComparisonRequest,
    PortfolioHistoricalPerformance,
    PortfolioOptimizationRequest,
    PortfolioPerformanceRequest,
    PortfolioPerformanceResponse,
    PortfolioRiskAnalysis,
    PortfolioStressTestResults,
    PortfolioSummary,
    RebalancingRecommendation,
)

# Position schemas
from backend.schemas.position import (
    BulkPositionUpdate,
    PositionAdjustment,
    PositionAllocation,
    PositionBase,
    PositionCreate,
    PositionFilters,
    PositionPerformanceMetrics,
    PositionResponse,
    PositionSummary,
    PositionUpdate,
)

# Transaction schemas
from backend.schemas.transaction import (
    BulkTransactionImport,
    BuyTransactionRequest,
    DividendTransactionRequest,
    SellTransactionRequest,
    TransactionBase,
    TransactionCreate,
    TransactionFilters,
    TransactionPerformanceMetrics,
    TransactionResponse,
    TransactionSummary,
    TransactionUpdate,
)

__all__ = [
    # Base schemas
    "BaseSchema",
    "TimestampMixin",
    "BaseResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthCheck",
    "StatusResponse",
    # Asset schemas
    "AssetBase",
    "AssetCreate",
    "AssetUpdate",
    "AssetMarketData",
    "AssetResponse",
    "AssetSummary",
    "AssetSearchParams",
    "AssetPriceUpdate",
    "BulkAssetPriceUpdate",
    # Position schemas
    "PositionBase",
    "PositionCreate",
    "PositionUpdate",
    "PositionResponse",
    "PositionSummary",
    "PositionFilters",
    "PositionAdjustment",
    "BulkPositionUpdate",
    "PositionPerformanceMetrics",
    "PositionAllocation",
    # Transaction schemas
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "TransactionSummary",
    "TransactionFilters",
    "BuyTransactionRequest",
    "SellTransactionRequest",
    "DividendTransactionRequest",
    "TransactionPerformanceMetrics",
    "BulkTransactionImport",
    # Portfolio schemas
    "PortfolioSummary",
    "AllocationBreakdown",
    "PerformanceMetrics",
    "PortfolioPerformanceRequest",
    "PortfolioPerformanceResponse",
    "PortfolioHistoricalPerformance",
    "DiversificationMetrics",
    "RebalancingRecommendation",
    "PortfolioOptimizationRequest",
    "PortfolioStressTestResults",
    "PortfolioAnalyticsResponse",
    "PortfolioComparisonRequest",
    "PortfolioRiskAnalysis",
]
