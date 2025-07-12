# OSINT Bot Mobile - Complete Deployment Guide

## Overview

This guide covers the complete deployment of the OSINT Bot mobile solution, including:
- Enhanced backend API with database management
- Mobile app for iOS content management
- Integration with existing OSINT bot system

## Architecture

```
Mobile App (iOS) ↔ Enhanced Backend API (Flask) ↔ Existing OSINT Bot ↔ Database (SQLite)
```

## Prerequisites

### System Requirements
- Python 3.8+
- Node.js 16+
- iOS development environment (Xcode, iOS Simulator)
- Git

### API Keys Required
- OpenAI API Key
- Telegram API credentials
- Bot Token

## Part 1: Backend Setup

### 1. Install Dependencies

```bash
# Install new Python dependencies
pip install flask flask-cors

# Update requirements.txt
echo "flask==2.3.3" >> requirements.txt
echo "flask-cors==4.0.0" >> requirements.txt
```

### 2. Database Setup

The system now uses SQLite for persistent storage. The database will be automatically created when you first run the API server.

### 3. Start the API Server

```bash
# Start the Flask API server
python api_server.py

# Or with custom port
PORT=8000 python api_server.py
```

The API will be available at `http://localhost:5000` (or your custom port).

### 4. Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get posts
curl http://localhost:5000/api/posts

# Get analytics
curl http://localhost:5000/api/analytics

# Get stats
curl http://localhost:5000/api/stats
```

## Part 2: Mobile App Setup

### 1. Install React Native CLI

```bash
npm install -g react-native-cli
```

### 2. Install Dependencies

```bash
cd mobile-app
npm install
```

### 3. iOS Setup

```bash
cd ios
pod install
cd ..
```

### 4. Configure API URL

Edit `mobile-app/src/context/ApiContext.tsx` and update the default API URL:

```typescript
const initialState: ApiState = {
  // ... other properties
  apiUrl: 'http://YOUR_SERVER_IP:5000', // Update this
};
```

### 5. Build and Run

```bash
# Start Metro bundler
npm start

# In another terminal, run iOS app
npm run ios

# Or run on specific device
npm run ios -- --device "iPhone 14"
```

## Part 3: Integration with Existing Bot

### 1. Update Bot Configuration

The existing bot has been enhanced to work with the new database system. No additional configuration is needed.

### 2. Run the Enhanced Bot

```bash
# Start the bot (now with database integration)
python main.py
```

The bot will now:
- Save all processed content to the database
- Calculate quality and bias scores
- Store metadata for mobile app access

## Part 4: Production Deployment

### Backend Deployment Options

#### Option 1: Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Option 2: Heroku
```bash
# Create Procfile
echo "web: python api_server.py" > Procfile

# Deploy to Heroku
heroku create osint-bot-api
git push heroku main
```

#### Option 3: VPS/Cloud Server
```bash
# Using systemd service
sudo nano /etc/systemd/system/osint-bot-api.service

[Unit]
Description=OSINT Bot API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/osint-bot
ExecStart=/usr/bin/python3 api_server.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable osint-bot-api
sudo systemctl start osint-bot-api
```

### Mobile App Deployment

#### iOS App Store Deployment

1. **Prepare for Release**
```bash
# Build release version
npm run build:ios:release
```

2. **Configure App Store Connect**
- Create app in App Store Connect
- Configure app metadata
- Upload screenshots

3. **Archive and Upload**
- Open project in Xcode
- Product → Archive
- Upload to App Store Connect

#### TestFlight Beta Distribution

1. **Configure Signing**
- Set up development team
- Configure provisioning profiles

2. **Upload to TestFlight**
- Archive in Xcode
- Upload to TestFlight
- Add beta testers

## Part 5: Configuration

### Environment Variables

Create `.env` file in the root directory:

```bash
# API Configuration
API_PORT=5000
DEBUG=false

# Database
DATABASE_PATH=osint_bot.db

# CORS Settings
CORS_ORIGINS=*

# Existing bot configuration
API_ID=your_api_id
API_HASH=your_api_hash
OPENAI_API_KEY=your_openai_key
BOT_TOKEN=your_bot_token
CHAT_ID=your_chat_id
```

### Mobile App Configuration

Update `mobile-app/src/config.ts`:

```typescript
export const config = {
  apiUrl: process.env.API_URL || 'http://localhost:5000',
  enablePushNotifications: true,
  autoRefreshInterval: 30000, // 30 seconds
  maxPostsPerPage: 50,
};
```

## Part 6: Monitoring and Maintenance

### Health Checks

```bash
# API health check
curl http://your-api-url/api/health

# Database health check
python -c "from database import DatabaseManager; db = DatabaseManager(); print('Database OK')"
```

### Log Monitoring

```bash
# View API logs
tail -f api.log

# View bot logs
tail -f bot.log

# View system logs
journalctl -u osint-bot-api -f
```

### Database Maintenance

```bash
# Backup database
cp osint_bot.db osint_bot_backup_$(date +%Y%m%d).db

# Clean up old posts (30+ days)
python -c "from database import DatabaseManager; db = DatabaseManager(); db.cleanup_old_posts(30)"

# Get database statistics
sqlite3 osint_bot.db "SELECT COUNT(*) FROM posts;"
```

## Part 7: Usage Guide

### Mobile App Features

1. **Posts Management**
   - View all processed posts
   - Filter by status (pending, posted, deleted, archived)
   - One-click Twitter posting
   - Batch operations

2. **Analytics Dashboard**
   - Performance metrics
   - Channel statistics
   - Quality scores
   - User action tracking

3. **Settings**
   - API configuration
   - Push notifications
   - Auto-refresh settings
   - Cache management

### API Endpoints

- `GET /api/health` - Health check
- `GET /api/posts` - Get posts with filtering
- `GET /api/posts/{id}` - Get specific post
- `POST /api/posts/{id}/action` - Perform action on post
- `POST /api/posts/batch-action` - Batch operations
- `GET /api/analytics` - Get analytics data
- `GET /api/stats` - Get quick statistics
- `GET /api/media/{filename}` - Serve media files
- `POST /api/cleanup` - Clean up old posts

## Part 8: Troubleshooting

### Common Issues

#### API Server Won't Start
```bash
# Check port availability
netstat -an | grep :5000

# Check Python dependencies
pip list | grep -E "(flask|cors)"

# Check database permissions
ls -la osint_bot.db
```

#### Mobile App Connection Issues
```bash
# Check network connectivity
ping your-api-server

# Check CORS configuration
curl -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET" -X OPTIONS http://your-api-url/api/health
```

#### Database Issues
```bash
# Check database integrity
sqlite3 osint_bot.db "PRAGMA integrity_check;"

# Reset database (WARNING: This will delete all data)
rm osint_bot.db
python -c "from database import DatabaseManager; DatabaseManager()"
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posts_quality ON posts(quality_score);
CREATE INDEX IF NOT EXISTS idx_posts_bias ON posts(bias_score);

-- Analyze database
ANALYZE;
```

#### API Optimization
```python
# Enable caching in api_server.py
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
def get_analytics():
    # ... existing code
```

## Part 9: Security Considerations

### API Security
- Use HTTPS in production
- Implement rate limiting
- Add authentication if needed
- Validate all inputs

### Mobile App Security
- Use secure API communication
- Implement certificate pinning
- Secure local storage
- Regular security updates

### Database Security
- Regular backups
- Access control
- Encryption at rest
- Audit logging

## Part 10: Support and Maintenance

### Regular Tasks
- Daily: Check logs and system health
- Weekly: Database backup and cleanup
- Monthly: Security updates and dependency updates
- Quarterly: Performance review and optimization

### Monitoring Setup
```bash
# Set up basic monitoring
crontab -e

# Add these lines:
# Check API health every 5 minutes
*/5 * * * * curl -f http://localhost:5000/api/health || echo "API down" | mail -s "OSINT Bot API Alert" admin@example.com

# Daily database backup
0 2 * * * cp /path/to/osint_bot.db /path/to/backups/osint_bot_$(date +\%Y\%m\%d).db
```

## Conclusion

This complete solution provides:
- Professional mobile interface for content management
- Robust backend API with database persistence
- Enhanced analytics and monitoring
- Scalable architecture for future growth

The system is now ready for production use with proper monitoring, security, and maintenance procedures in place. 