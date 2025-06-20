# Technical Debt and Issues Audit

## Date: 2025-06-17

This document summarizes the remaining technical debt and issues found in the Financial Dashboard codebase after the recent cleanup efforts.

## Critical Issues

### 1. SQLAlchemy Compatibility Issue
**File:** `backend/models/isin.py`
**Line:** 51-57
**Issue:** The `postgresql_where` parameter in UniqueConstraint is not accepted by the current SQLAlchemy version
**Impact:** Tests cannot run, imports fail
**Fix Required:** Update the constraint syntax to be compatible with SQLAlchemy 2.0+

### 2. Undefined Logger Variable
**File:** `start_services.py`
**Lines:** 183, 187
**Issue:** Using `logger` variable without importing or defining it
**Impact:** Script will crash if health check fails
**Fix Required:** Add logger import or remove logger calls

## Minor Issues

### 3. NotImplementedError in Base Class
**File:** `backend/services/market_data.py`
**Line:** 51
**Issue:** `MarketDataProvider.fetch_quote()` raises NotImplementedError
**Impact:** None - this is a base class method meant to be overridden
**Status:** Acceptable pattern for abstract base class

### 4. SQLAlchemy Deprecation Warnings
**File:** `backend/models/base.py`
**Line:** 26
**Issue:** Using deprecated `as_declarative()` function
**Impact:** Will break in SQLAlchemy 3.0
**Fix Required:** Update to use `declarative_base()` or modern declarative mapping

### 5. Test Marker Warnings
**Issue:** Undefined pytest marks (unit, financial, slow)
**Impact:** Warning messages during test runs
**Fix Required:** Register custom marks in pytest.ini

## Test Status

- Basic tests are passing (6/6)
- Many test files have import errors due to SQLAlchemy issue
- 103 tests collected, but 8 collection errors preventing full test suite execution

## Configuration Issues

### 6. Pydantic V2 Migration
**Issue:** Some models still using class-based config (deprecated in Pydantic V2)
**Impact:** Deprecation warnings
**Fix Required:** Update to use ConfigDict

## Summary

The codebase is generally well-structured with most TODO/FIXME comments addressed. The main blocking issues are:

1. **SQLAlchemy constraint syntax** - Prevents tests from running
2. **Logger import in start_services.py** - Will cause runtime error

Once these two issues are fixed, the codebase should be in good shape for continued development. The other issues are minor and can be addressed as part of normal maintenance.

## Recommendations

1. **Immediate Actions:**
   - Fix SQLAlchemy UniqueConstraint syntax
   - Add logger import to start_services.py
   - Run full test suite to identify any other issues

2. **Short-term Actions:**
   - Update SQLAlchemy declarative base usage
   - Register pytest markers
   - Complete Pydantic V2 migration

3. **Long-term Actions:**
   - Monitor for new deprecation warnings
   - Keep dependencies updated
   - Maintain test coverage above 80%
