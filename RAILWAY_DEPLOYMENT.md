# 🚂 Railway Deployment Guide

This guide will help you deploy your OSINT Bot to Railway.app platform.

## 📋 Prerequisites

1. **GitHub Account**: Your code must be in a GitHub repository
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **Environment Variables**: All your API keys and credentials ready
4. **Session File**: Your Telegram session file (`multi_session.session`)

## 🔧 Pre-Deployment Setup

### 1. Session File Encoding

Your Telegram session file needs to be converted to base64 for Railway deployment:

```bash
# On Windows PowerShell
$bytes = [System.IO.File]::ReadAllBytes("multi_session.session")
$base64 = [System.Convert]::ToBase64String($bytes)
Write-Output $base64
```

```bash
# On Linux/Mac
base64 -w 0 multi_session.session
```

Copy the output - you'll need this for the `SESSION_B64` environment variable.

### 2. Required Environment Variables

Prepare these environment variables for Railway:

```env
# Telegram API Configuration
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash

# OpenAI API Configuration  
OPENAI_API_KEY=your_openai_api_key

# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_target_chat_id

# JWT Authentication
JWT_SECRET_KEY=your_strong_jwt_secret_key

# Session File (Base64 encoded)
SESSION_B64=your_base64_encoded_session_file

# Optional
CSV_FILE=gpt_full_log.csv
```

## 🚀 Deployment Steps

### Step 1: Push to GitHub

1. **Add all files to git:**
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Verify sensitive files are ignored:**
   - `.env` file should NOT be in the repository
   - `*.session` files should NOT be in the repository
   - Check your `.gitignore` file includes these patterns

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your OSINT bot repository
5. Railway will automatically detect it's a Python project

### Step 3: Configure Environment Variables

1. In your Railway project dashboard, go to **"Variables"** tab
2. Add all the environment variables listed above
3. **Important**: Make sure to set the `SESSION_B64` variable with your base64-encoded session file

### Step 4: Configure Services

Railway will automatically create a **Web Service** for your API server. You need to add a **Worker Service** for the bot:

1. **Web Service** (Automatic):
   - Command: `python api_server.py`
   - Port: 5000
   - This handles the API and dashboard

2. **Worker Service** (Manual):
   - Click **"+ New Service"**
   - Choose **"Empty Service"**
   - Go to **"Settings"** → **"Service"**
   - Set **Start Command**: `python main.py`
   - This runs the Telegram bot

### Step 5: Domain Configuration (Optional)

1. In the **Web Service**, go to **"Settings"** → **"Networking"**
2. Click **"Generate Domain"** to get a public URL
3. Your dashboard will be available at: `https://your-app.railway.app`

## 🔍 Monitoring and Troubleshooting

### Check Logs

1. **Web Service Logs**: Check API server status and HTTP requests
2. **Worker Service Logs**: Check bot activity and Telegram messages

### Common Issues

1. **Session Authentication Failed**:
   - Verify `SESSION_B64` is correctly encoded
   - Check `API_ID` and `API_HASH` are correct
   - Ensure session file is not corrupted

2. **Database Issues**:
   - Railway provides persistent storage
   - Database will be created automatically on first run

3. **Rate Limiting**:
   - Monitor API usage in logs
   - Adjust `LOOP_INTERVAL` if needed

4. **Memory Issues**:
   - Railway free tier has memory limits
   - Monitor resource usage in dashboard

## 📊 Project Structure

```
osint-bot/
├── api_server.py          # Flask API server (Web Service)
├── main.py               # Telegram bot (Worker Service)
├── bot.py                # Bot logic
├── config.py             # Configuration with Railway support
├── database.py           # Database management
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── Procfile             # Railway process configuration
├── railway.json         # Railway deployment config
├── nixpacks.toml        # Build configuration
├── mobile-app/          # Dashboard frontend
└── media/               # Media files storage
```

## 🔒 Security Notes

1. **Never commit sensitive files**:
   - `.env` files
   - Session files (`*.session`)
   - Database files (`*.db`)

2. **Environment Variables**:
   - Use Railway's environment variables for all secrets
   - Never hardcode API keys in code

3. **Session File**:
   - Keep your session file secure
   - Regenerate if compromised
   - Use base64 encoding for deployment

## 💰 Cost Considerations

### Railway Free Tier
- **$5 credit per month**
- **500 hours of usage**
- **1GB RAM per service**
- **1GB storage**

### Optimization Tips
- Monitor resource usage regularly
- Use efficient polling intervals
- Implement proper error handling
- Consider upgrading if you hit limits

## 📈 Scaling

As your bot grows, consider:

1. **Database Optimization**:
   - Regular cleanup of old posts
   - Indexing for better performance

2. **Resource Monitoring**:
   - Track memory and CPU usage
   - Optimize media handling

3. **Multiple Instances**:
   - Scale web service for high traffic
   - Keep worker service as single instance

## 🆘 Support

If you encounter issues:

1. **Check Railway Logs**: Most issues are visible in service logs
2. **Review Environment Variables**: Ensure all required variables are set
3. **Verify GitHub Repository**: Make sure all files are committed
4. **Test Locally**: Verify the bot works locally before deploying

## 🎉 Post-Deployment

After successful deployment:

1. **Test the Dashboard**: Visit your Railway domain
2. **Verify Bot Activity**: Check worker service logs
3. **Monitor Performance**: Keep an eye on resource usage
4. **Update Documentation**: Note your deployment URL and settings

Your OSINT bot is now running on Railway! 🚀

---

**Note**: This deployment uses Railway's free tier. Monitor your usage to avoid unexpected charges. 