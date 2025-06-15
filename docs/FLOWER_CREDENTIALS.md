# Flower UI Credentials Management Guide

## 🌸 Flower Monitoring Dashboard

Flower is the web-based monitoring tool for Celery tasks, accessible at http://localhost:5555. It provides real-time monitoring of your background task processing.

## 🔑 Default Credentials

**Username:** `admin`
**Password:** `admin`

## 🌐 How to Access Flower

### Method 1: Web Browser
1. Open your web browser
2. Navigate to: http://localhost:5555
3. Enter credentials when prompted:
   - **Username:** `admin`
   - **Password:** `admin`

### Method 2: Command Line Test
```bash
# Test access
curl -u admin:admin http://localhost:5555

# Check if Flower is healthy
./scripts/services.sh health
```

## 🔧 Changing Credentials

### Option 1: Environment Variables (Recommended)

Add to your `.env` file:
```bash
# Flower UI Credentials
FLOWER_USERNAME=your_username
FLOWER_PASSWORD=your_secure_password
```

Then restart Flower:
```bash
./scripts/services.sh restart flower
```

### Option 2: Direct Script Modification

Edit `scripts/services.sh` line ~385:
```bash
# Find this line:
--basic_auth=admin:admin

# Change to:
--basic_auth=your_username:your_password
```

Then restart Flower:
```bash
./scripts/services.sh restart flower
```

## 🛡️ Security Recommendations

### For Development
- Default credentials (`admin:admin`) are fine for local development
- Ensure Flower is only accessible from localhost

### For Production
- **Always change default credentials**
- Use strong passwords
- Consider additional authentication layers
- Restrict network access to authorized users

### Example Secure Credentials
```bash
# In .env file
FLOWER_USERNAME=flower_monitor
FLOWER_PASSWORD=SecureP@ssw0rd123!
```

## 📊 What You Can Monitor in Flower

### Real-time Information
- **Active Tasks**: Currently running background tasks
- **Task History**: Completed, failed, and retried tasks
- **Worker Status**: Health and performance of Celery workers
- **Queue Status**: Task queue lengths and processing rates

### Key Metrics
- **Task Throughput**: Tasks processed per second
- **Success/Failure Rates**: Task completion statistics
- **Runtime Statistics**: Task execution times
- **Worker Load**: CPU and memory usage per worker

## 🔍 Common Flower Use Cases

### 1. Monitor Portfolio Updates
- Check if market data updates are running
- Monitor portfolio calculation tasks
- Track data synchronization jobs

### 2. Debug Task Issues
- View failed task details and error messages
- Monitor task retry attempts
- Check task execution times

### 3. Performance Monitoring
- Track worker performance
- Monitor queue backlogs
- Identify bottlenecks

## 🚨 Troubleshooting Access Issues

### Can't Access Flower UI

1. **Check if Flower is running:**
   ```bash
   ./scripts/services.sh status
   ```

2. **Check port availability:**
   ```bash
   lsof -i :5555
   ```

3. **Restart Flower:**
   ```bash
   ./scripts/services.sh restart flower
   ```

### Authentication Errors

1. **Verify credentials:**
   ```bash
   # Check what credentials are being used
   ./scripts/services.sh urls
   ```

2. **Test with curl:**
   ```bash
   curl -u admin:admin http://localhost:5555
   ```

3. **Check Flower logs:**
   ```bash
   ./scripts/services.sh logs flower
   ```

### Browser Issues

1. **Clear browser cache** and try again
2. **Try incognito/private mode**
3. **Test with different browser**

## 📱 Alternative Access Methods

### API Access
Flower also provides a REST API:
```bash
# Get worker statistics
curl -u admin:admin http://localhost:5555/api/workers

# Get active tasks
curl -u admin:admin http://localhost:5555/api/tasks

# Get worker information
curl -u admin:admin http://localhost:5555/api/workers?status=1
```

### Command Line Monitoring
```bash
# Check Celery workers directly
cd /path/to/financial-dashboard-mcp
python -m celery -A backend.tasks inspect active

# Check registered tasks
python -m celery -A backend.tasks inspect registered
```

## 🔄 Updating Credentials

### Step-by-Step Process

1. **Update credentials:**
   ```bash
   # Edit .env file
   nano .env

   # Add or modify:
   FLOWER_USERNAME=new_username
   FLOWER_PASSWORD=new_password
   ```

2. **Restart Flower:**
   ```bash
   ./scripts/services.sh restart flower
   ```

3. **Verify new credentials:**
   ```bash
   # Check the new credentials are shown
   ./scripts/services.sh urls

   # Test access
   curl -u new_username:new_password http://localhost:5555
   ```

4. **Update bookmarks/scripts** that use the old credentials

## 📋 Quick Reference

| Action | Command |
|--------|---------|
| **Access Flower** | http://localhost:5555 |
| **Default Login** | admin / admin |
| **Check Status** | `./scripts/services.sh status` |
| **Restart Flower** | `./scripts/services.sh restart flower` |
| **View Logs** | `./scripts/services.sh logs flower` |
| **Test API** | `curl -u admin:admin http://localhost:5555/api/workers` |

## 🎯 Best Practices

1. **Change default credentials** before exposing to network
2. **Use environment variables** for credential management
3. **Regularly monitor** task performance and failures
4. **Keep Flower updated** with your Celery version
5. **Backup important task data** shown in Flower
6. **Document any custom credentials** for your team

The Flower UI is an essential tool for monitoring your Financial Dashboard's background task processing. Proper credential management ensures secure access while maintaining visibility into your system's performance.
