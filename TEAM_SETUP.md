# Team Setup Guide

Flow Guardian supports team knowledge sharing through three deployment patterns.

## Overview

Team features allow multiple developers to:
- Share learnings and insights
- Search across team's collective knowledge
- Maintain project-wide context
- Collaborate on documentation

## Architecture Options

### Option 1: Shared Network Drive (Simplest)

**Best for:** Small teams with shared network storage

All team members point to the same SQLite database on a shared drive.

#### Setup

```bash
# 1. Choose shared location
SHARED_DIR=/Volumes/TeamDrive/flow-guardian

# 2. Configure each team member's .env
export FLOW_GUARDIAN_DATA_DIR=$SHARED_DIR

# 3. Run Flow Guardian normally
python server.py all
```

#### Pros
- No server setup required
- File-based, simple to understand
- Works offline (if drive is mounted)

#### Cons
- Requires shared network drive
- No concurrent writes (SQLite limitation)
- Network latency affects performance

---

### Option 2: Central Server (Recommended)

**Best for:** Teams of any size, remote teams

One team member (or dedicated server) hosts Flow Guardian. Others connect via HTTP.

#### Setup

**Server Setup:**

```bash
# 1. On server machine (team-server.local)
cp .env.example .env
# Add API keys to .env

# 2. Start server (accessible to network)
python server.py all --host 0.0.0.0 --port 8090

# 3. Verify it's running
curl http://localhost:8090/health
```

**Client Setup:**

```bash
# 1. On each client machine
cp .env.example .env
# Add API keys to .env

# 2. Add team server URL
echo "FLOW_GUARDIAN_TEAM_URL=http://team-server.local:8090" >> .env

# 3. Run Flow Guardian locally (for personal memory)
python server.py all

# 4. Use team search
flow team "authentication patterns"
```

#### Pros
- True multi-user support
- Central source of truth
- No network drive needed
- Concurrent access supported

#### Cons
- Requires always-on server
- Network dependency
- Need to manage server

#### Advanced: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLOW_GUARDIAN_DATA_DIR=/data
VOLUME /data

EXPOSE 8090

CMD ["python", "server.py", "all", "--host", "0.0.0.0"]
```

```bash
# Build and run
docker build -t flow-guardian .
docker run -d \
  -p 8090:8090 \
  -v flow-data:/data \
  -e CEREBRAS_API_KEY=csk-... \
  -e GEMINI_API_KEY=... \
  --name flow-guardian \
  flow-guardian
```

---

### Option 3: Hybrid (Personal + Team)

**Best for:** Teams wanting fast local access + shared knowledge

Each person runs their own server for personal memory, but queries team server for shared knowledge.

#### Setup

**Each Team Member:**

```bash
# .env
CEREBRAS_API_KEY=csk-...
GEMINI_API_KEY=...
FLOW_GUARDIAN_USER=yourname
FLOW_GUARDIAN_TEAM_URL=http://team-server:8090
```

**Usage:**

```bash
# Personal search (fast, local)
flow recall "my authentication notes"

# Team search (queries team server)
flow team "authentication patterns"

# Share with team
flow learn "Use RS256 for JWT signing" --team
```

#### Pros
- Fast local search
- Shared team knowledge
- Best of both worlds

#### Cons
- More complex setup
- Two databases to manage

---

## Security Considerations

Flow Guardian has **no built-in authentication**. Use these patterns for security:

### 1. Private Network Only

Run on VPN or local network:

```bash
# Server binds to private IP only
python server.py all --host 192.168.1.100
```

### 2. SSH Tunnel

Access remote server via SSH:

```bash
# On client
ssh -L 8090:localhost:8090 user@team-server

# In .env
FLOW_GUARDIAN_TEAM_URL=http://localhost:8090
```

### 3. Reverse Proxy with Auth

Use nginx + HTTP basic auth:

```nginx
# /etc/nginx/sites-available/flow-guardian
server {
    listen 80;
    server_name flow.yourcompany.com;

    auth_basic "Flow Guardian";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd teamuser
```

### 4. Tailscale/ZeroTier

Use mesh VPN for secure access:

```bash
# Install Tailscale on server
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# Server accessible at: http://team-server.tail-scale.ts.net:8090
```

---

## Team Workflows

### Sharing Learnings

```bash
# Individual stores personal learning
flow learn "Found bug in JWT validation" --tag auth

# Share important learnings with team
flow learn "Use RS256 for production JWT" --team --tag auth
```

### Team Search

```bash
# Search team knowledge
flow team "database migration patterns"

# In Claude Code
"What does the team know about database migrations?"
# Claude uses: flow_team("database migration patterns")
```

### Session Capture

```bash
# Personal sessions stay local
flow save -m "Fixed authentication bug"

# Team can search if you shared learnings
flow learn "Auth bug was timezone issue" --team
```

---

## Monitoring & Maintenance

### Server Health Check

```bash
# Check if server is running
curl http://team-server:8090/health

# Get status
curl http://team-server:8090/status
```

### View Server Logs

```bash
# On server
tail -f ~/.flow-guardian/daemon/server.log
```

### Backup Team Data

```bash
# On server
tar -czf flow-guardian-backup-$(date +%Y%m%d).tar.gz ~/.flow-guardian/
```

### Restore from Backup

```bash
# On server
tar -xzf flow-guardian-backup-20260201.tar.gz -C ~/
```

---

## Troubleshooting

### "Team not configured"

**Problem:** `flow team` says team not configured

**Solution:**
```bash
# Add to .env
FLOW_GUARDIAN_TEAM_URL=http://team-server:8090
```

### "Connection refused"

**Problem:** Can't connect to team server

**Solutions:**
1. Check server is running: `curl http://team-server:8090/health`
2. Check firewall: `sudo ufw allow 8090`
3. Check network: `ping team-server`
4. Use IP instead of hostname: `http://192.168.1.100:8090`

### "Slow team searches"

**Problem:** Team queries are slow

**Solutions:**
1. Check network latency: `ping team-server`
2. Run server on faster hardware
3. Use hybrid mode (local + team)
4. Consider shared network drive for small teams

### "API key errors on server"

**Problem:** Server can't access Cerebras/Gemini

**Solution:**
```bash
# On server, verify .env
cat .env | grep API_KEY

# Restart server
python server.py stop
python server.py all --foreground
```

---

## Example Configurations

### Small Startup (3-5 people)

```bash
# Shared network drive
# Each dev's .env:
FLOW_GUARDIAN_DATA_DIR=/Volumes/CompanyDrive/flow-guardian
```

### Remote Team (10+ people)

```bash
# Central server (cloud VM)
# Server: AWS EC2, DigitalOcean Droplet
# Clients: Team URL in .env
FLOW_GUARDIAN_TEAM_URL=https://flow.company.com
```

### Hybrid Setup (consulting team)

```bash
# Each consultant runs local instance
# Company runs central server for shared patterns
FLOW_GUARDIAN_TEAM_URL=http://company-server:8090
```

---

## Migration from v1.0 (Backboard)

If you were using Backboard team threads:

### Old (v1.0):
```bash
BACKBOARD_TEAM_THREAD_ID=thread_abc123
```

### New (v2.0):
```bash
FLOW_GUARDIAN_TEAM_URL=http://team-server:8090
```

Data is **not** automatically migrated from Backboard. Team knowledge needs to be rebuilt locally.

---

## Questions?

- **Issues:** https://github.com/yourusername/flow-guardian/issues
- **Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Setup:** See [SETUP.md](SETUP.md)
