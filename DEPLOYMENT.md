# 🚀 Advanced Discord RPG Bot - Deployment Guide

This guide covers deploying the advanced Discord RPG bot with all its new features including guilds, PvP arena, crafting, and trading systems.

## 📋 Prerequisites

### System Requirements
- **Python 3.11+** (required for advanced features)
- **Discord Bot Token** with appropriate permissions
- **Database** (PostgreSQL recommended for production)
- **Redis** (for caching and session management)
- **Memory**: 512MB+ RAM
- **Storage**: 1GB+ for logs and data

### Discord Bot Permissions
```
Required Permissions:
✅ Send Messages
✅ Use Slash Commands
✅ Embed Links
✅ Attach Files
✅ Read Message History
✅ Add Reactions
✅ Use External Emojis
✅ Manage Messages (for cleanup)
```

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd discord-rpg-bot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create `.env` file in project root:
```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_client_id_here
BOT_PREFIX=!

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/rpgbot
MONGODB_URL=mongodb://localhost:27017/rpgbot
REDIS_URL=redis://localhost:6379

# AI/LLM Configuration (optional)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Webhook Configuration (optional)
WEBHOOK_URL=your_webhook_url_here

# Game Configuration
DEBUG_MODE=False
MAX_LEVEL=100
XP_MULTIPLIER=1.0
GOLD_MULTIPLIER=1.0

# Advanced Features
ENABLE_GUILDS=True
ENABLE_PVP=True
ENABLE_CRAFTING=True
ENABLE_TRADING=True
```

## 🗄️ Database Setup

### PostgreSQL (Recommended)
```sql
-- Create database
CREATE DATABASE rpgbot;

-- Create user (optional)
CREATE USER rpgbot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE rpgbot TO rpgbot_user;
```

### MongoDB (Optional)
```bash
# Install MongoDB
sudo apt-get install mongodb

# Start MongoDB service
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

### Redis (Required for caching)
```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## 🚀 Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

EXPOSE 8080

CMD ["python", "main.py"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  rpgbot:
    build: .
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    ports:
      - "8080:8080"

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=rpgbot
      - POSTGRES_USER=rpgbot_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### Deploy with Docker
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f rpgbot

# Stop services
docker-compose down
```

### Option 2: Systemd Service (Linux)

#### Create service file
```bash
sudo nano /etc/systemd/system/discord-rpg-bot.service
```

#### Service configuration
```ini
[Unit]
Description=Discord RPG Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/discord-rpg-bot
Environment=PATH=/opt/discord-rpg-bot/venv/bin
ExecStart=/opt/discord-rpg-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and start service
```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-rpg-bot
sudo systemctl start discord-rpg-bot
sudo systemctl status discord-rpg-bot
```

### Option 3: PM2 (Node.js Process Manager)

#### Install PM2
```bash
npm install -g pm2
```

#### Create ecosystem file
```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'discord-rpg-bot',
    script: 'main.py',
    interpreter: 'python3',
    cwd: '/opt/discord-rpg-bot',
    env: {
      NODE_ENV: 'production',
      DISCORD_TOKEN: 'your_token_here'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
  }]
};
```

#### Start with PM2
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 📊 Monitoring & Observability

### Health Checks
```python
# Add to main.py
@app.route('/health')
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "systems": {
            "database": await check_database_connection(),
            "redis": await check_redis_connection(),
            "discord": bot.is_ready()
        }
    }
```

### Logging Configuration
```python
# Enhanced logging for production
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/bot.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Metrics Collection
```python
# Add metrics collection
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
commands_total = Counter('discord_commands_total', 'Total commands executed', ['command'])
command_duration = Histogram('discord_command_duration_seconds', 'Command execution time')
guild_activities = Counter('guild_activities_total', 'Guild activities started', ['activity_type'])
pvp_matches = Counter('pvp_matches_total', 'PvP matches played', ['match_type'])
```

## 🔧 Advanced Configuration

### Guild System Settings
```python
# config.py additions
GUILD_MAX_MEMBERS = 30
GUILD_LEVEL_REQUIREMENTS = {
    1: {"xp_required": 0, "member_limit": 10},
    2: {"xp_required": 1000, "member_limit": 15},
    3: {"xp_required": 2500, "member_limit": 20},
    4: {"xp_required": 5000, "member_limit": 25},
    5: {"xp_required": 10000, "member_limit": 30}
}
```

### PvP Arena Settings
```python
# PvP configuration
PVP_RANK_THRESHOLDS = {
    "bronze": {"min": 0, "max": 999, "multiplier": 1.0},
    "silver": {"min": 1000, "max": 1999, "multiplier": 1.1},
    "gold": {"min": 2000, "max": 2999, "multiplier": 1.2},
    "platinum": {"min": 3000, "max": 3999, "multiplier": 1.3},
    "diamond": {"min": 4000, "max": 4999, "multiplier": 1.4},
    "master": {"min": 5000, "max": 5999, "multiplier": 1.5},
    "grandmaster": {"min": 6000, "max": float('inf'), "multiplier": 2.0}
}
```

### Crafting System Settings
```python
# Crafting configuration
CRAFTING_DIFFICULTY_MULTIPLIERS = {
    "easy": 1.0,
    "medium": 1.2,
    "hard": 1.5,
    "expert": 2.0,
    "master": 3.0
}

MARKET_SETTINGS = {
    "listing_expiry_days": 7,
    "max_listings_per_user": 10,
    "market_fee_percentage": 0.05
}
```

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use secrets management for production
- Rotate Discord tokens regularly

### Database Security
```sql
-- Create read-only user for analytics
CREATE USER rpgbot_readonly WITH PASSWORD 'readonly_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rpgbot_readonly;
```

### Network Security
```bash
# Firewall rules
sudo ufw allow 22/tcp
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 6379/tcp  # Redis
sudo ufw enable
```

## 📈 Performance Optimization

### Database Indexing
```sql
-- Add indexes for common queries
CREATE INDEX idx_players_guild_id ON players(guild_id);
CREATE INDEX idx_guild_activities_guild_id ON guild_activities(guild_id);
CREATE INDEX idx_pvp_matches_player_id ON pvp_matches(player1_id, player2_id);
CREATE INDEX idx_market_listings_status ON market_listings(status);
```

### Caching Strategy
```python
# Redis caching for frequently accessed data
async def get_cached_player_data(user_id: int):
    cache_key = f"player:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    player_data = await db.get_player(user_id)
    await redis.setex(cache_key, 300, json.dumps(player_data))  # 5 min cache
    return player_data
```

### Rate Limiting
```python
# Enhanced rate limiting for advanced features
RATE_LIMITS = {
    "guild_raid": {"calls": 1, "period": 3600},  # 1 per hour
    "pvp_challenge": {"calls": 5, "period": 300},  # 5 per 5 min
    "market_listing": {"calls": 10, "period": 3600},  # 10 per hour
    "crafting": {"calls": 20, "period": 3600}  # 20 per hour
}
```

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check bot status
docker-compose logs rpgbot
# or
sudo systemctl status discord-rpg-bot

# Check Discord API
curl -H "Authorization: Bot YOUR_TOKEN" https://discord.com/api/v10/gateway/bot
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U rpgbot_user -d rpgbot -c "SELECT 1;"

# Check Redis connection
redis-cli ping
```

#### Memory Issues
```bash
# Monitor memory usage
htop
# or
docker stats

# Check for memory leaks
python -m memory_profiler main.py
```

### Log Analysis
```bash
# View recent errors
grep "ERROR" logs/bot.log | tail -20

# Monitor guild activities
grep "guild_raid" logs/bot.log | tail -10

# Check PvP activity
grep "pvp_match" logs/bot.log | tail -10
```

## 📚 Maintenance

### Regular Tasks
- **Daily**: Check bot status and error logs
- **Weekly**: Review performance metrics and database size
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and optimize database queries

### Backup Strategy
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
pg_dump rpgbot > $BACKUP_DIR/rpgbot_$DATE.sql

# Configuration backup
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env data/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Update Procedure
```bash
# 1. Stop the bot
docker-compose down
# or
sudo systemctl stop discord-rpg-bot

# 2. Backup current data
./backup.sh

# 3. Pull latest code
git pull origin main

# 4. Update dependencies
pip install -r requirements.txt

# 5. Run migrations (if any)
python migrations/run_migrations.py

# 6. Restart the bot
docker-compose up -d
# or
sudo systemctl start discord-rpg-bot

# 7. Verify functionality
python test_advanced_features.py
```

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] Database setup and indexed
- [ ] Redis caching enabled
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Security measures in place
- [ ] Rate limiting configured
- [ ] Health checks working
- [ ] Error handling tested
- [ ] Performance optimized
- [ ] Documentation updated

## 📞 Support

For issues and questions:
- Check the logs first: `docker-compose logs rpgbot`
- Review this deployment guide
- Test with the provided test suite: `python test_advanced_features.py`
- Create detailed bug reports with logs and reproduction steps

---

**Happy Deploying! 🚀**
