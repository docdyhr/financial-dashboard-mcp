# Claude Desktop Usage Guide

Complete guide to using the Financial Dashboard MCP with Claude Desktop for natural language portfolio management.

## 🚀 Overview

The Financial Dashboard MCP integration transforms Claude Desktop into your personal AI financial advisor. You can manage your entire investment portfolio through natural conversation - add positions, track performance, get recommendations, and analyze risk without ever leaving Claude.

## 📋 Prerequisites

Before using the Claude Desktop integration, ensure you have:

1. ✅ **Financial Dashboard running**: `./scripts/start_dashboard.sh`
2. ✅ **MCP server configured**: See [MCP Setup Guide](MCP_SETUP.md)
3. ✅ **Claude Desktop installed** with our MCP server configured
4. ✅ **Internet connection** for real-time market data

## 🛠️ Available Tools (13 MCP Tools)

### **Portfolio Management (5 tools)**
- **`get_positions`** - View current holdings with real-time values
- **`get_portfolio_summary`** - Overall portfolio metrics and performance
- **`get_allocation`** - Asset allocation breakdown by sector/type
- **`add_position`** ⭐ - **Add new ticker symbols and positions**
- **`update_position`** ⭐ - **Modify existing positions**

### **Market Data & Analytics (4 tools)**
- **`get_asset_price`** - Real-time prices for any ticker
- **`calculate_performance`** - Performance analytics across timeframes
- **`analyze_portfolio_risk`** - Risk assessment and volatility metrics
- **`get_market_trends`** - Current market and sector trends

### **AI-Powered Insights (4 tools)**
- **`recommend_allocation`** - AI portfolio allocation recommendations
- **`analyze_opportunity`** - Investment opportunity discovery
- **`rebalance_portfolio`** - Smart rebalancing suggestions
- **`ai_insights`** - Advanced portfolio analysis

## 📊 Complete Usage Examples

### **🏁 Getting Started: Your First Portfolio**

**You:** "I want to start tracking my investment portfolio. Can you help me add some positions?"

**Claude:** I'd be happy to help you manage your investment portfolio! Let me first check your current positions and then we can add new ones.

*Claude checks your current portfolio*

**Claude:** I see you're starting fresh - perfect! What positions would you like to add?

**You:** "I bought 100 shares of Apple at $180 per share yesterday, and 50 shares of Microsoft at $320 per share last week."

**Claude:** Excellent choices! Let me add these positions to your portfolio.

*Claude adds both positions with accurate details*

**Claude:** ✅ **Successfully added your positions:**

- **Apple (AAPL)**: 100 shares @ $180.00 = $18,000
- **Microsoft (MSFT)**: 50 shares @ $320.00 = $16,000

**Total Invested**: $34,000

Would you like me to check how they're performing right now?

---

### **💰 Real-Time Performance Tracking**

**You:** "How are my positions performing today?"

**Claude:** Let me check the current prices and calculate your performance.

*Claude gets real-time prices and calculates performance*

**Claude:** **📈 Current Portfolio Performance:**

**Today's Performance:**
- **AAPL**: 100 shares @ $185.50 = $18,550 (**+$550**, +3.06%)
- **MSFT**: 50 shares @ $315.20 = $15,760 (**-$240**, -1.50%)

**Portfolio Summary:**
- **Current Value**: $34,310
- **Total Gain/Loss**: **+$310** (+0.91%)
- **Best Performer**: Apple (+3.06%)
- **Today's Change**: +$125 (+0.36%)

---

### **📈 Adding Multiple Positions**

**You:** "I want to diversify. Add 75 shares of NVIDIA at $450, 50 shares of Johnson & Johnson at $160, and 25 shares of Coca-Cola at $58."

**Claude:** Great diversification strategy! Let me add these three new positions across different sectors.

*Claude adds all three positions*

**Claude:** ✅ **Added your diversification positions:**

**New Positions:**
- **NVIDIA (NVDA)**: 75 shares @ $450.00 = $33,750 (Technology)
- **Johnson & Johnson (JNJ)**: 50 shares @ $160.00 = $8,000 (Healthcare)
- **Coca-Cola (KO)**: 25 shares @ $58.00 = $1,450 (Consumer Staples)

**📊 Updated Portfolio Allocation:**
- **Technology**: 70.8% ($51,550)
- **Healthcare**: 11.0% ($8,000)
- **Consumer Staples**: 2.0% ($1,450)
- **Total Value**: $72,760

Your portfolio is now more diversified across sectors!

---

### **🔄 Updating Positions**

**You:** "I made a mistake - I actually bought 30 shares of Coca-Cola, not 25. Can you update that?"

**Claude:** No problem! Let me correct your Coca-Cola position.

*Claude updates the position*

**Claude:** ✅ **Updated Coca-Cola position:**
- **Previous**: 25 shares @ $58.00 = $1,450
- **Corrected**: 30 shares @ $58.00 = $1,740
- **Difference**: +$290

Your portfolio value is now **$73,050**.

---

### **🎯 Investment Recommendations**

**You:** "I have $10,000 more to invest. What do you recommend for a moderate risk tolerance?"

**Claude:** Let me analyze your current allocation and provide personalized recommendations.

*Claude analyzes current portfolio and generates recommendations*

**Claude:** **💡 Investment Recommendations for $10,000:**

**Current Allocation Analysis:**
- Technology: 70.8% (Overweight)
- Healthcare: 11.0% (Good)
- Consumer Staples: 2.4% (Underweight)
- **Missing**: Financials, International, Bonds

**Recommended Allocations:**
1. **International ETF (VXUS)**: $3,000 (30%)
2. **Financial Sector (JPM or BAC)**: $2,500 (25%)
3. **Bond ETF (AGG)**: $2,000 (20%)
4. **Energy Sector (XOM)**: $1,500 (15%)
5. **Additional Healthcare (UNH)**: $1,000 (10%)

This would create a more balanced portfolio with better diversification.

---

### **📊 Performance Analysis**

**You:** "How has my portfolio performed over the last 6 months?"

**Claude:** Let me analyze your portfolio's 6-month performance.

*Claude calculates detailed performance metrics*

**Claude:** **📈 6-Month Portfolio Performance Analysis:**

**Overall Performance:**
- **Starting Value**: $70,000 (estimated based on purchase dates)
- **Current Value**: $73,050
- **Total Return**: +$3,050 (+4.36%)
- **Annualized Return**: +8.72%

**Individual Position Performance:**
- **AAPL**: +12.5% (Best performer)
- **NVDA**: +8.2% (Strong growth)
- **MSFT**: +2.1% (Steady gains)
- **JNJ**: +1.8% (Stable dividend stock)
- **KO**: +0.5% (Defensive position)

**Risk Metrics:**
- **Portfolio Beta**: 1.12 (Slightly more volatile than market)
- **Sharpe Ratio**: 0.78 (Good risk-adjusted returns)
- **Maximum Drawdown**: -8.4% (October dip)

**Benchmark Comparison:**
- **S&P 500**: +3.2% (You're outperforming! 🎉)

---

### **🔍 Market Opportunities**

**You:** "What are some good investment opportunities right now?"

**Claude:** Let me analyze current market trends and find opportunities that fit your portfolio.

*Claude analyzes market trends and identifies opportunities*

**Claude:** **🌟 Current Market Opportunities:**

**Trending Sectors:**
1. **Artificial Intelligence**: +15% this quarter
2. **Clean Energy**: Growing on policy support
3. **Healthcare Technology**: Aging population driver
4. **Infrastructure**: Government spending boost

**🎯 Specific Opportunities:**
1. **Tesla (TSLA)** - $240
   - Clean energy leader, down 8% this week
   - Good entry point for EV exposure

2. **Palantir (PLTR)** - $18
   - AI/data analytics leader
   - Strong government contracts

3. **Moderna (MRNA)** - $85
   - Healthcare innovation beyond COVID
   - Undervalued on recent dip

4. **Brookfield Renewable (BEP)** - $28
   - Clean energy infrastructure
   - 5.5% dividend yield

**💡 Recommendation**: Consider adding TSLA for tech diversification and BEP for yield + growth.

---

### **⚖️ Portfolio Rebalancing**

**You:** "Should I rebalance my portfolio?"

**Claude:** Let me analyze your current allocation and provide rebalancing recommendations.

*Claude analyzes portfolio balance and generates rebalancing strategy*

**Claude:** **⚖️ Portfolio Rebalancing Analysis:**

**Current vs. Target Allocation:**
- **Technology**: 70.8% → Target: 60% (**Overweight by 10.8%**)
- **Healthcare**: 11.0% → Target: 15% (**Underweight by 4%**)
- **Consumer Staples**: 2.4% → Target: 5% (**Underweight by 2.6%**)
- **Missing Sectors**: Financials (10%), International (10%)

**📋 Rebalancing Recommendations:**

**Sell (Reduce Technology):**
- Sell 15 shares of NVDA (~$6,975)
- This reduces tech allocation to ~61%

**Buy (Add Missing Sectors):**
- **JPMorgan (JPM)**: $2,500 (Financials)
- **Vanguard International (VXUS)**: $2,500 (International)
- **Procter & Gamble (PG)**: $1,975 (Consumer Staples)

**Expected Outcome:**
- **Technology**: 61% ✅
- **Healthcare**: 11% ✅
- **Financials**: 7% ✅
- **International**: 7% ✅
- **Consumer Staples**: 5% ✅

This creates a more balanced, lower-risk portfolio.

---

### **🚨 Risk Analysis**

**You:** "How risky is my current portfolio?"

**Claude:** Let me perform a comprehensive risk analysis of your portfolio.

*Claude analyzes portfolio risk metrics*

**Claude:** **🔍 Portfolio Risk Analysis:**

**Risk Level**: **Moderate-High**

**Key Risk Metrics:**
- **Portfolio Beta**: 1.18 (18% more volatile than market)
- **Standard Deviation**: 22.4% (annual volatility)
- **Value at Risk (95%)**: -$3,200 daily maximum loss
- **Sharpe Ratio**: 0.82 (Good risk-adjusted returns)

**Risk Factors:**
1. **Technology Concentration**: 70.8% in one sector
2. **Large-Cap Bias**: 89% in large companies
3. **US-Only Exposure**: No international diversification
4. **Growth Tilt**: Limited value/dividend stocks

**Risk Recommendations:**
1. **Reduce tech concentration** to <60%
2. **Add international exposure** (15-20%)
3. **Include defensive sectors** (utilities, consumer staples)
4. **Consider bonds** for stability (10-20%)

**Stress Test Results:**
- **2008 Crisis Scenario**: -42% portfolio decline
- **COVID-19 Scenario**: -28% portfolio decline
- **Tech Bubble Scenario**: -35% portfolio decline

**💡 Overall**: Your portfolio has good return potential but could benefit from more diversification to reduce risk.

---

## 🎯 Natural Language Commands

You can use natural, conversational language with Claude. Here are examples:

### **Adding Positions**
- *"Add 100 shares of Apple at $180"*
- *"I bought Tesla yesterday for $240 per share, 50 shares"*
- *"Add AAPL 100 shares $180 purchased 2024-01-15"*
- *"Buy 50 Microsoft at market price"*

### **Portfolio Queries**
- *"Show me my current positions"*
- *"What's my portfolio worth today?"*
- *"How am I performing this month?"*
- *"What's my biggest position?"*

### **Updates and Corrections**
- *"Update my Microsoft position - I actually have 75 shares, not 50"*
- *"Change my Apple purchase price to $175"*
- *"I sold 25 shares of Tesla yesterday"*

### **Analysis Requests**
- *"Analyze my portfolio risk"*
- *"How diversified am I?"*
- *"What sectors am I missing?"*
- *"Should I rebalance?"*

### **Investment Research**
- *"What crypto should I add to diversify?"*
- *"Show me dividend stocks under $50"*
- *"Find growth stocks in healthcare"*
- *"What are the best performing sectors this year?"*

### **Market Insights**
- *"What's happening in the markets today?"*
- *"How has my tech allocation performed this quarter?"*
- *"Find me some undervalued opportunities"*
- *"What are analysts saying about AI stocks?"*

## 🎨 Advanced Use Cases

### **Asset Classes Supported**
- **US Stocks**: AAPL, MSFT, GOOGL, etc.
- **ETFs**: SPY, QQQ, VTI, VXUS, etc.
- **International**: Use appropriate ticker symbols
- **Cryptocurrency**: BTC-USD, ETH-USD, etc.
- **Bonds**: AGG, TLT, etc.

### **Time Horizons**
- **Real-time**: Current prices and daily changes
- **Short-term**: 1D, 1W, 1M performance
- **Medium-term**: 3M, 6M analysis
- **Long-term**: 1Y, YTD, since inception

### **Portfolio Strategies**
- **Growth Investing**: Focus on capital appreciation
- **Value Investing**: Undervalued opportunity identification
- **Income Investing**: Dividend and yield analysis
- **Index Investing**: ETF and passive strategy recommendations
- **Sector Rotation**: Market timing and sector analysis

## 🛠️ Troubleshooting

### **Common Issues**

**❌ "Tool not found" error**
- Ensure the Financial Dashboard is running (`./scripts/start_dashboard.sh`)
- Check MCP server configuration in Claude Desktop
- Restart Claude Desktop if needed

**❌ "Unable to get market data"**
- Check internet connection
- Some tickers may not be available (check symbol format)
- Market may be closed (prices from last close)

**❌ "Position not found"**
- Use `get_positions` to see available positions
- Check ticker symbol spelling
- Position may need to be added first

### **Best Practices**

✅ **Start each session** with "Show me my current portfolio"
✅ **Use standard ticker symbols** (AAPL not Apple Inc.)
✅ **Include purchase dates** for accurate tracking
✅ **Regular portfolio reviews** weekly or monthly
✅ **Diversification checks** across sectors and asset classes

## 📚 Additional Resources

- **[Quick Start Guide](QUICK_START.md)** - Getting the dashboard running
- **[MCP Setup Guide](MCP_SETUP.md)** - Detailed Claude Desktop configuration
- **[MCP Troubleshooting](MCP_TROUBLESHOOTING.md)** - Common issues and solutions
- **[Frontend Guide](FRONTEND_GUIDE.md)** - Using the web dashboard
- **[API Documentation](http://localhost:8000/docs)** - Backend API reference

## 🎉 Next Steps

1. **Try it out**: Start with "Show me my current portfolio"
2. **Add your positions**: Use natural language to add your holdings
3. **Explore analysis**: Ask for performance metrics and recommendations
4. **Set up regular reviews**: Weekly portfolio check-ins with Claude
5. **Advanced strategies**: Explore rebalancing and opportunity analysis

---

**Happy Investing! 📈**

Transform your portfolio management experience with AI-powered natural language conversations through Claude Desktop.
```

Now I'll update the README to link to this new guide:
