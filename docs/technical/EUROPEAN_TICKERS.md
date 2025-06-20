# European Ticker Support Guide

This guide explains how European and international tickers are supported in the Financial Dashboard MCP system.

## Overview

The Financial Dashboard now provides comprehensive support for European and international stock tickers through enhanced ticker parsing, validation, and market data fetching capabilities.

## Supported Exchange Formats

### European Exchanges

| Exchange | Suffix | Example | Currency | Country |
|----------|--------|---------|----------|---------|
| London Stock Exchange | `.L` | `VODAFONE.L` | GBP | GB |
| Euronext Paris | `.PA` | `ASML.PA` | EUR | FR |
| Frankfurt/XETRA | `.DE` | `SAP.DE` | EUR | DE |
| Borsa Italiana (Milan) | `.MI` | `FERRARI.MI` | EUR | IT |
| Euronext Amsterdam | `.AS` | `SHELL.AS` | EUR | NL |
| Euronext Brussels | `.BR` | `ACKERMANS.BR` | EUR | BE |
| Euronext Lisbon | `.LS` | `GALP.LS` | EUR | PT |
| Bolsa de Madrid | `.MC` | `SANTANDER.MC` | EUR | ES |
| Wiener Börse (Vienna) | `.VI` | `VOEST.VI` | EUR | AT |
| SIX Swiss Exchange | `.SW` | `NESTLE.SW` | CHF | CH |

### Nordic Exchanges

| Exchange | Suffix | Example | Currency | Country |
|----------|--------|---------|----------|---------|
| Nasdaq Stockholm | `.ST` | `VOLVO-B.ST` | SEK | SE |
| Nasdaq Helsinki | `.HE` | `NOKIA.HE` | EUR | FI |
| Oslo Børs | `.OL` | `EQUINOR.OL` | NOK | NO |
| Nasdaq Copenhagen | `.CO` | `NOVO-B.CO` | DKK | DK |
| Nasdaq Iceland | `.IC` | `MAREL.IC` | ISK | IS |

### Other International Exchanges

| Exchange | Suffix | Example | Currency | Country |
|----------|--------|---------|----------|---------|
| Toronto Stock Exchange | `.TO` | `SHOPIFY.TO` | CAD | CA |
| TSX Venture Exchange | `.V` | `EXAMPLE.V` | CAD | CA |
| Australian Securities Exchange | `.AX` | `CBA.AX` | AUD | AU |
| Tokyo Stock Exchange | `.T` | `TOYOTA.T` | JPY | JP |
| Hong Kong Stock Exchange | `.HK` | `TENCENT.HK` | HKD | HK |
| Singapore Exchange | `.SG` | `DBS.SG` | SGD | SG |
| National Stock Exchange of India | `.NS` | `RELIANCE.NS` | INR | IN |
| Bombay Stock Exchange | `.BO` | `TCS.BO` | INR | IN |
| B3 (Brazil) | `.SA` | `VALE.SA` | BRL | BR |

## Ticker Format Rules

### International Tickers
- Format: `BASE_TICKER.EXCHANGE_SUFFIX`
- Base ticker: 1-15 alphanumeric characters
- Exchange suffix: 1-3 alphabetic characters
- Example: `ASML.PA`, `VODAFONE.L`, `SAP.DE`

### US Tickers
- Format: `TICKER` (no suffix)
- Length: 1-10 alphanumeric characters
- Example: `AAPL`, `MSFT`, `GOOGL`

## Usage Examples

### Adding European Assets

```python
from backend.schemas.asset import AssetCreate
from backend.models.asset import AssetType, AssetCategory

# London Stock Exchange
vodafone = AssetCreate(
    ticker="VODAFONE.L",
    name="Vodafone Group Plc",
    asset_type=AssetType.STOCK,
    category=AssetCategory.EQUITY,
    exchange="London Stock Exchange",
    currency="GBP",
    country="GB",
    sector="Telecommunications"
)

# Euronext Paris
asml = AssetCreate(
    ticker="ASML.PA",
    name="ASML Holding N.V.",
    asset_type=AssetType.STOCK,
    category=AssetCategory.EQUITY,
    exchange="Euronext Paris",
    currency="EUR",
    country="NL",
    sector="Technology"
)

# Frankfurt/XETRA
sap = AssetCreate(
    ticker="SAP.DE",
    name="SAP SE",
    asset_type=AssetType.STOCK,
    category=AssetCategory.EQUITY,
    exchange="Frankfurt/XETRA",
    currency="EUR",
    country="DE",
    sector="Software"
)
```

### Market Data Fetching

The system automatically handles ticker formatting for different data providers:

```python
from backend.services.market_data import MultiProviderMarketDataService

# Initialize market data service
market_service = MultiProviderMarketDataService()

# Fetch European ticker data
result = market_service.fetch_quote("ASML.PA")
if result.success:
    print(f"ASML Price: €{result.current_price}")
else:
    print(f"Error: {result.error}")
```

### Ticker Validation

```python
from backend.services.ticker_utils import TickerUtils

# Validate ticker format
is_valid, error = TickerUtils.validate_ticker_format("ASML.PA")
if is_valid:
    print("Valid ticker format")
else:
    print(f"Invalid: {error}")

# Parse ticker information
ticker_info = TickerUtils.parse_ticker("ASML.PA")
print(f"Exchange: {ticker_info.exchange_name}")
print(f"Currency: {ticker_info.default_currency}")
print(f"Country: {ticker_info.country_code}")
```

## API Provider Support

### Yahoo Finance (Primary)
- **Supported**: All European and international exchanges
- **Format**: Uses original ticker format (e.g., `ASML.PA`)
- **Reliability**: High for major European stocks
- **Rate Limits**: Minimal

### Alpha Vantage (Fallback)
- **Supported**: Most international exchanges
- **Format**: Uses original ticker format
- **Reliability**: Good for major stocks
- **Rate Limits**: 5 calls per minute (free tier)

### Finnhub (Additional)
- **Supported**: Major European exchanges
- **Format**: Varies by exchange
- **Reliability**: Good for real-time data
- **Rate Limits**: 60 calls per minute (free tier)

## Common European Ticker Examples

### Blue Chip European Stocks

```
# United Kingdom
VODAFONE.L     - Vodafone Group
BP.L           - BP plc
SHELL.L        - Shell plc
BARC.L         - Barclays
LLOY.L         - Lloyds Banking Group

# France
ASML.PA        - ASML Holding
LVMH.PA        - LVMH
TOTALENERGIES.PA - TotalEnergies
SANOFI.PA      - Sanofi
LOREAL.PA      - L'Oréal

# Germany
SAP.DE         - SAP SE
ADIDAS.DE      - Adidas AG
BMW.DE         - BMW AG
SIEMENS.DE     - Siemens AG
MERCEDES-BENZ.DE - Mercedes-Benz Group

# Netherlands
ASML.AS        - ASML Holding (also on Amsterdam)
SHELL.AS       - Shell plc (also on Amsterdam)
UNILEVER.AS    - Unilever N.V.

# Italy
FERRARI.MI     - Ferrari N.V.
ENEL.MI        - Enel SpA
INTESA.MI      - Intesa Sanpaolo

# Switzerland
NESTLE.SW      - Nestlé S.A.
NOVARTIS.SW    - Novartis AG
ROCHE.SW       - Roche Holding AG
```

## Troubleshooting

### Common Issues

1. **Ticker Not Found**
   - Verify the correct exchange suffix
   - Check if the company is publicly traded
   - Try alternative exchange listings

2. **Data Provider Errors**
   - Different providers may use different ticker formats
   - Some providers have limited international coverage
   - Check API key configuration for paid providers

3. **Currency Handling**
   - Prices are returned in the exchange's native currency
   - Currency conversion is not automatic
   - Set the asset's currency field correctly

### Testing Your Tickers

Use the provided test script to validate European ticker support:

```bash
cd financial-dashboard-mcp
python scripts/test_european_tickers.py
```

This script will:
- Validate ticker formats
- Test ticker parsing
- Show supported exchanges
- Optionally test live market data fetching

## Best Practices

### Ticker Selection
1. **Use the primary exchange** for the most liquid market
2. **Consider currency** when adding international assets
3. **Verify ticker symbols** on the exchange's official website
4. **Use consistent formatting** across your portfolio

### Data Quality
1. **Monitor data provider reliability** for international tickers
2. **Set up multiple providers** for critical assets
3. **Regularly validate** ticker symbols haven't changed
4. **Consider time zone differences** for market hours

### Portfolio Management
1. **Group by currency** for better analysis
2. **Consider exchange rate impacts** on performance
3. **Monitor international market hours** for updates
4. **Use local market analysis** for European stocks

## Support and Updates

The ticker utilities are designed to be extensible. New exchanges can be added by updating the `EXCHANGE_INFO` dictionary in `backend/services/ticker_utils.py`.

For additional exchange support or ticker format issues, please:
1. Check the existing supported exchanges list
2. Verify the ticker format with the exchange
3. Test with the provided scripts
4. Submit a feature request with exchange details

## Related Documentation

- [Market Data Service](./MARKET_DATA.md)
- [Asset Management](./ASSETS.md)
- [API Configuration](./API_CONFIG.md)
- [Testing Guide](./TESTING.md)
