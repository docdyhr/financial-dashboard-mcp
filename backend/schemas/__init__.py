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
    "AllocationBreakdown",
    # Asset schemas
    "AssetBase",
    "AssetCreate",
    "AssetMarketData",
    "AssetPriceUpdate",
    "AssetResponse",
    "AssetSearchParams",
    "AssetSummary",
    "AssetUpdate",
    "BaseResponse",
    # Base schemas
    "BaseSchema",
    "BulkAssetPriceUpdate",
    "BulkPositionUpdate",
    "BulkTransactionImport",
    "BuyTransactionRequest",
    "DiversificationMetrics",
    "DividendTransactionRequest",
    "ErrorResponse",
    "HealthCheck",
    "PaginatedResponse",
    "PaginationParams",
    "PerformanceMetrics",
    "PortfolioAnalyticsResponse",
    "PortfolioComparisonRequest",
    "PortfolioHistoricalPerformance",
    "PortfolioOptimizationRequest",
    "PortfolioPerformanceRequest",
    "PortfolioPerformanceResponse",
    "PortfolioRiskAnalysis",
    "PortfolioStressTestResults",
    # Portfolio schemas
    "PortfolioSummary",
    "PositionAdjustment",
    "PositionAllocation",
    # Position schemas
    "PositionBase",
    "PositionCreate",
    "PositionFilters",
    "PositionPerformanceMetrics",
    "PositionResponse",
    "PositionSummary",
    "PositionUpdate",
    "RebalancingRecommendation",
    "SellTransactionRequest",
    "StatusResponse",
    "TimestampMixin",
    # Transaction schemas
    "TransactionBase",
    "TransactionCreate",
    "TransactionFilters",
    "TransactionPerformanceMetrics",
    "TransactionResponse",
    "TransactionSummary",
    "TransactionUpdate",
]
