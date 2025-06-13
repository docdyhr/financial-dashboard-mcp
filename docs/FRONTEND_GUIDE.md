# Financial Dashboard Frontend Guide

## Overview

The Financial Dashboard frontend is built with Streamlit and provides a comprehensive interface for portfolio management, task monitoring, and analytics. It connects to the FastAPI backend through REST APIs and provides real-time data visualization.

## Features

### 🏠 Dashboard Page
- **Portfolio Overview**: Total value, cash position, number of positions, YTD return
- **Performance Metrics**: Configurable time periods (1D, 1W, 1M, 3M, 6M, 1Y, YTD)
- **Asset Allocation Chart**: Interactive pie chart showing portfolio distribution
- **Holdings Table**: Real-time position data with P&L calculations
- **Portfolio Value Chart**: Historical portfolio performance
- **Data Refresh Controls**: Manual refresh and snapshot creation

### 📊 Portfolio Page
- **Current Holdings**: Detailed table with market values and performance
- **Add Position**: Form to add new investments with validation
- **Transaction History**: Track all portfolio changes (coming soon)

### ⚙️ Tasks Page
- **System Status**: Real-time health monitoring of all services
- **Active Tasks**: Monitor running background tasks
- **Task Submission**: Submit market data, analytics, and snapshot tasks
- **Task History**: Review completed tasks and their results

### 📈 Analytics Page
- **Performance Analysis**: Detailed metrics with multiple time periods
- **Risk Metrics**: Portfolio beta, VaR, max drawdown (placeholder)
- **Benchmarking**: Compare against market indices (coming soon)

### ⚙️ Settings Page
- **General Settings**: Theme, currency, date format preferences
- **Data Sources**: Configure market data providers and update frequency
- **Notifications**: Email alerts and notification preferences

## Quick Start

### 1. Start the Complete System

```bash
# Method 1: Use the startup script (recommended)
./scripts/start_dashboard.sh

# Method 2: Manual startup
# Terminal 1: Start backend services
docker-compose up -d

# Terminal 2: Start frontend
cd frontend
streamlit run app.py
```

### 2. Add Sample Data

```bash
# Run the demo setup script to populate with sample data
python scripts/demo_setup.py
```

### 3. Access the Dashboard

Open your browser and navigate to:
- **Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Task Monitor**: http://localhost:5555

## Component Architecture

### Portfolio Components (`components/portfolio.py`)

#### Key Functions:
- `portfolio_overview_widget()`: Main dashboard metrics
- `performance_metrics_widget()`: Performance analysis with time period selection
- `asset_allocation_chart()`: Interactive pie chart for allocation
- `holdings_table()`: Real-time holdings with P&L
- `portfolio_value_chart()`: Historical value tracking
- `refresh_data_button()`: Data refresh and task submission

#### API Integration:
- `GET /api/portfolio/summary`: Portfolio overview data
- `GET /api/portfolio/positions`: Current holdings
- `GET /api/portfolio/performance`: Performance metrics
- `POST /api/tasks/market-data/update-prices`: Trigger data refresh
- `POST /api/tasks/portfolio/snapshot`: Create portfolio snapshot

### Task Components (`components/tasks.py`)

#### Key Functions:
- `task_monitoring_widget()`: Display active tasks
- `submit_task_widget()`: Submit new background tasks
- `system_status_widget()`: Service health monitoring
- `task_history_widget()`: Recent task history

#### API Integration:
- `GET /api/tasks/active`: List running tasks
- `GET /api/tasks/{task_id}/status`: Check task status
- `POST /api/tasks/market-data/fetch`: Submit market data tasks
- `POST /api/tasks/portfolio/analytics`: Submit analytics tasks

## Configuration

### Environment Variables

```bash
# Backend connection
BACKEND_URL=http://localhost:8000

# Streamlit configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Streamlit Configuration

The app is configured with:
- **Wide layout**: Full-width pages for better data visualization
- **Expanded sidebar**: Always-visible navigation
- **Custom page config**: Optimized for financial dashboard use

## Data Flow

1. **User Interaction**: User interacts with Streamlit interface
2. **API Calls**: Frontend makes HTTP requests to FastAPI backend
3. **Real-time Updates**: Data refreshes through manual refresh or auto-refresh
4. **Task Integration**: Submit background tasks and monitor progress
5. **Visual Updates**: Charts and tables update with new data

## Key Features

### Real-time Data Refresh
- Manual refresh button triggers market data updates
- Automatic snapshot creation for portfolio tracking
- Live task monitoring with status updates

### Interactive Charts
- **Plotly Integration**: Interactive charts with zoom, pan, hover
- **Responsive Design**: Charts adapt to container width
- **Color Coding**: Visual indicators for positive/negative performance

### Task Management
- Submit market data fetch tasks for specific symbols
- Create portfolio snapshots on demand
- Run analytics tasks and monitor progress
- View task history and results

### Error Handling
- Backend connectivity checks
- Graceful degradation when services are unavailable
- User-friendly error messages
- Retry mechanisms for failed requests

## Customization

### Adding New Components

1. Create component functions in `components/` directory
2. Import and use in main `app.py`
3. Follow the pattern of API integration with error handling

### Styling
- Streamlit's built-in theming system
- Custom CSS through `st.markdown()` for advanced styling
- Consistent color scheme for financial data

### API Integration
- All API calls include timeout handling
- Consistent error message format
- Graceful handling of backend unavailability

## Troubleshooting

### Common Issues

1. **Backend Not Accessible**
   - Check if Docker services are running: `docker-compose ps`
   - Verify backend health: `curl http://localhost:8000/health`
   - Check network connectivity and port availability

2. **No Data Displayed**
   - Run demo setup script: `python scripts/demo_setup.py`
   - Check if positions exist: `curl http://localhost:8000/api/portfolio/positions`
   - Trigger market data update through Tasks page

3. **Charts Not Loading**
   - Ensure Plotly is installed: `pip install plotly`
   - Check browser console for JavaScript errors
   - Verify data format from API endpoints

4. **Tasks Not Working**
   - Check Celery worker status: `docker-compose logs celery-worker`
   - Verify Redis connectivity: `redis-cli ping`
   - Check task queue through Flower: http://localhost:5555

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance

### Optimization Tips
- Use `@st.cache_data` for expensive API calls
- Implement pagination for large datasets
- Use background tasks for heavy computations
- Optimize chart rendering with appropriate data sampling

### Resource Usage
- Frontend: ~50-100MB RAM
- Real-time updates: Minimal CPU overhead
- Network: Efficient API calls with caching

## Future Enhancements

### Planned Features
- WebSocket integration for real-time updates
- Advanced filtering and search capabilities
- Export functionality (PDF, Excel)
- Mobile-responsive design improvements
- Custom dashboard layouts
- Integration with additional data sources

### Technical Improvements
- React/Next.js migration path
- Progressive Web App (PWA) features
- Offline functionality
- Advanced caching strategies
- Performance monitoring integration

## Support

For issues and feature requests:
1. Check the troubleshooting section above
2. Review API documentation at http://localhost:8000/docs
3. Check task queue status at http://localhost:5555
4. Examine Docker logs: `docker-compose logs`

---

This frontend provides a comprehensive interface for financial portfolio management with real-time data integration and task queue monitoring. The modular component architecture makes it easy to extend and customize for specific needs.
