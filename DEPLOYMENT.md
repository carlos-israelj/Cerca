# Production Deployment Guide

This guide covers deploying Cerca to production on **Render** with production-grade reliability, security, and monitoring.

---

## Architecture Overview

Cerca deploys as **two services** on Render:

```
┌─────────────────────────────────────────────────────────┐
│                    Render Platform                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐         ┌────────────────────┐  │
│  │ Web Service      │         │  Worker Service    │  │
│  │ (webhook.py)     │         │  (scheduler.py)    │  │
│  │                  │         │                    │  │
│  │ FastAPI app      │         │ APScheduler        │  │
│  │ Public HTTPS URL │         │ Background process │  │
│  │ Health checks    │         │ Triggers calls     │  │
│  └──────────────────┘         └────────────────────┘  │
│           │                            │               │
│           │                            │               │
└───────────┼────────────────────────────┼───────────────┘
            │                            │
            ▼                            ▼
    ┌───────────────┐          ┌──────────────────┐
    │  ElevenLabs   │          │   ElevenLabs     │
    │  (webhooks)   │          │   (outbound API) │
    └───────────────┘          └──────────────────┘
            │
            ▼
    ┌───────────────┐
    │    Twilio     │
    │  (WhatsApp)   │
    └───────────────┘
```

---

## Prerequisites

Before deploying:

1. **Accounts**
   - [Render account](https://render.com) (free tier works for pilot)
   - [ElevenLabs account](https://elevenlabs.io) with configured agent
   - [Twilio account](https://www.twilio.com) with phone number and WhatsApp

2. **Configuration Ready**
   - Agent configured in ElevenLabs (see `agent/agent_config.md`)
   - `contacts.json` populated with real contacts
   - All environment variables collected

3. **GitHub Repository**
   - Code pushed to GitHub (Render deploys from Git)

---

## Step 1: Prepare Configuration Files

### 1.1 Create `render.yaml`

Create this file in the repository root:

```yaml
services:
  # Webhook API - Handles ElevenLabs callbacks
  - type: web
    name: cerca-webhook
    env: python
    region: oregon
    plan: starter  # Free tier OK for pilot
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.webhook:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: ELEVENLABS_API_KEY
        sync: false
      - key: ELEVENLABS_AGENT_ID
        sync: false
      - key: ELEVENLABS_AGENT_PHONE_NUMBER_ID
        sync: false
      - key: ELEVENLABS_WEBHOOK_SECRET
        sync: false
      - key: TWILIO_ACCOUNT_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false
      - key: TWILIO_WHATSAPP_FROM
        sync: false
      - key: FALLBACK_FAMILY_WHATSAPP
        sync: false
    healthCheckPath: /health

  # Scheduler - Triggers daily calls
  - type: worker
    name: cerca-scheduler
    env: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: python app/scheduler.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: ELEVENLABS_API_KEY
        sync: false
      - key: ELEVENLABS_AGENT_ID
        sync: false
      - key: ELEVENLABS_AGENT_PHONE_NUMBER_ID
        sync: false
      - key: TWILIO_ACCOUNT_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false
      - key: TWILIO_WHATSAPP_FROM
        sync: false
      - key: FALLBACK_FAMILY_WHATSAPP
        sync: false
```

### 1.2 Update `.gitignore`

Ensure sensitive files are ignored (already configured):

```
.env
app/memory.json
```

### 1.3 Commit Changes

```bash
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

---

## Step 2: Deploy to Render

### 2.1 Create New Web Service

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml` and create both services

### 2.2 Configure Environment Variables

For **both services** (webhook and scheduler), add these environment variables:

| Variable | Value | Where to Find |
|----------|-------|---------------|
| `ELEVENLABS_API_KEY` | `sk_...` | ElevenLabs Dashboard → Settings → API Keys |
| `ELEVENLABS_AGENT_ID` | `agent_...` | ElevenLabs Agents Dashboard → Your Agent → ID |
| `ELEVENLABS_AGENT_PHONE_NUMBER_ID` | `phnum_...` | Agent → Phone Numbers → ID |
| `ELEVENLABS_WEBHOOK_SECRET` | `wsec_...` | Agent → Webhooks → Secret |
| `TWILIO_ACCOUNT_SID` | `AC...` | Twilio Console → Account Info |
| `TWILIO_AUTH_TOKEN` | `...` | Twilio Console → Auth Token |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` | Twilio → WhatsApp Senders |
| `FALLBACK_FAMILY_WHATSAPP` | `whatsapp:+1...` | Your fallback number (optional) |

**Security Best Practice:**
- Mark all variables as **"Secret"** in Render
- Never commit these to Git

### 2.3 Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repo
   - Install dependencies
   - Start both services
   - Assign a public URL to the webhook service

### 2.4 Note Your Webhook URL

After deployment, copy your webhook URL:
```
https://cerca-webhook.onrender.com
```

---

## Step 3: Configure ElevenLabs Webhook

### 3.1 Set Webhook URL

1. Go to [ElevenLabs Agents Dashboard](https://elevenlabs.io/app/conversational-ai)
2. Open your Cerca agent
3. Go to **Settings → Webhooks**
4. Set **Post-call webhook URL:**
   ```
   https://cerca-webhook.onrender.com/webhook/elevenlabs
   ```
5. Save and copy the **Webhook Secret**
6. Add the secret to Render environment variables as `ELEVENLABS_WEBHOOK_SECRET`

### 3.2 Test Webhook

Trigger a test call:

```bash
# From your local machine
curl -X POST https://cerca-webhook.onrender.com/health
# Should return: {"status":"ok","service":"cerca-webhook"}
```

---

## Step 4: Production Contacts Configuration

### 4.1 Update Contacts

Ensure `app/contacts.json` has real, production-ready contacts:

```json
{
  "contacts": [
    {
      "id": "contact_001",
      "active": true,
      "elder_name": "María González",
      "elder_phone": "+593991234567",
      "family_name": "Carlos",
      "family_whatsapp": "whatsapp:+11234567890",
      "timezone": "America/Guayaquil",
      "call_time": "09:00",
      "medications": [
        {
          "name": "Losartán cincuenta miligramos",
          "time": "09:00",
          "note": "para la presión arterial"
        }
      ],
      "topics": [
        "sus plantas de tomate",
        "su nieto Mateo",
        "el clima en Cuenca"
      ],
      "notes": "Vive sola. Hijo vive en EE.UU."
    }
  ]
}
```

**Important:**
- Write medication names phonetically for natural pronunciation
- Use timezone of the elderly person's location
- Test with family member's real WhatsApp first

### 4.2 Commit and Deploy

```bash
git add app/contacts.json
git commit -m "Update production contacts"
git push origin main
```

Render will auto-redeploy both services.

---

## Step 5: Testing in Production

### 5.1 Health Check

```bash
curl https://cerca-webhook.onrender.com/health
```

Expected:
```json
{"status":"ok","service":"cerca-webhook"}
```

### 5.2 Manual Call Test

Option A: From Render Dashboard
1. Go to **cerca-scheduler** service
2. Open **Shell**
3. Run: `python app/caller.py contact_001`

Option B: From local machine (if you have .env configured):
```bash
python app/caller.py contact_001
```

### 5.3 Verify Full Flow

1. Call is received by elderly person
2. Conversation happens (check ElevenLabs dashboard for logs)
3. After call ends, webhook is triggered
4. WhatsApp summary arrives at family member's phone
5. Memory is saved for next call

### 5.4 Check Logs

In Render Dashboard:
- **cerca-webhook**: View HTTP requests and webhook processing
- **cerca-scheduler**: View scheduled call triggers

---

## Step 6: Monitoring and Maintenance

### 6.1 Set Up Monitoring

**Render Built-in:**
- **Metrics:** CPU, memory, request rate (Dashboard → Metrics tab)
- **Logs:** Real-time logs (Dashboard → Logs tab)
- **Alerts:** Email notifications on service failures

**External (Optional):**
- **UptimeRobot** or **Better Uptime**: Health check monitoring
- **Sentry**: Error tracking and alerting
- **DataDog/New Relic**: APM for production

### 6.2 Log Monitoring

Check logs regularly for:
- Failed calls (connection issues, wrong numbers)
- Webhook errors (signature failures, network issues)
- Memory file corruption warnings

### 6.3 Regular Tasks

**Daily:**
- Verify scheduler is running
- Check webhook health endpoint

**Weekly:**
- Review call logs in ElevenLabs dashboard
- Verify WhatsApp deliveries
- Check for memory.json growth

**Monthly:**
- Review and rotate logs
- Update dependencies: `pip list --outdated`
- Clean up old data per retention policy

---

## Step 7: Scaling Beyond Pilot

### 7.1 When to Scale

Consider upgrading when:
- **>10 contacts** → Starter plan may be slow
- **>50 contacts** → Need Professional plan
- **>500 contacts** → Switch to database backend

### 7.2 Horizontal Scaling

Render allows horizontal scaling:

```yaml
# In render.yaml, add:
services:
  - type: web
    name: cerca-webhook
    # ... other config ...
    scaling:
      minInstances: 2
      maxInstances: 10
      targetMemoryPercent: 70
      targetCPUPercent: 70
```

### 7.3 Database Migration

For 100+ contacts, migrate to PostgreSQL:

1. Add Render PostgreSQL service
2. Replace `contacts.json` with database tables
3. Replace `memory.json` with Redis cache
4. Encrypt PHI (medication data)

See `CLAUDE.md` section 15 for database schema design.

---

## Step 8: Troubleshooting

### Common Issues

#### Webhook Returns 401 Unauthorized
- **Cause:** Incorrect webhook secret
- **Fix:** Verify `ELEVENLABS_WEBHOOK_SECRET` matches ElevenLabs dashboard

#### Calls Not Being Scheduled
- **Cause:** Scheduler service not running or timezone mismatch
- **Fix:**
  1. Check Render logs for scheduler service
  2. Verify `call_time` and `timezone` in contacts.json
  3. Restart scheduler service

#### WhatsApp Not Delivered
- **Cause:** Twilio sandbox not approved or wrong number format
- **Fix:**
  1. Verify number format: `whatsapp:+1234567890`
  2. Check Twilio logs for delivery status
  3. Ensure WhatsApp sender is approved

#### Memory Not Persisting
- **Cause:** Render ephemeral filesystem (files don't persist across deploys)
- **Fix:** Use persistent disk or external storage (Redis, S3)

**Enable Persistent Disk in Render:**
```yaml
# In render.yaml
services:
  - type: web
    name: cerca-webhook
    disk:
      name: cerca-data
      mountPath: /opt/render/project/src/app
      sizeGB: 1
```

#### Agent Doesn't Remember Previous Calls
- **Cause:** `memory.json` not being read/written correctly
- **Fix:** Check webhook logs for save_last_summary errors

---

## Step 9: Security Hardening

### 9.1 API Key Rotation

Rotate keys quarterly:

1. Generate new keys in ElevenLabs/Twilio
2. Update Render environment variables
3. Test with new keys
4. Revoke old keys

### 9.2 IP Whitelisting (Optional)

Restrict webhook to ElevenLabs IPs only:

```python
# In webhook.py
ALLOWED_IPS = [
    "54.x.x.x",  # ElevenLabs egress IPs
    # Get from ElevenLabs support
]

@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        return JSONResponse({"error": "Forbidden"}, status_code=403)
    return await call_next(request)
```

### 9.3 Rate Limiting

Add rate limiting to webhook:

```bash
pip install slowapi
```

```python
# In webhook.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/webhook/elevenlabs")
@limiter.limit("100/minute")
async def elevenlabs_webhook(request: Request):
    # ... existing code
```

---

## Step 10: Cost Optimization

### Current Costs (Pilot)

| Service | Plan | Cost/Month |
|---------|------|------------|
| Render Web Service | Starter | Free (or $7) |
| Render Worker | Starter | Free (or $7) |
| ElevenLabs (5 min/day × 30 days) | Pay-as-you-go | ~$45 |
| Twilio (calls + WhatsApp) | Pay-as-you-go | ~$15 |
| **Total** | | **~$60-74/month** |

### At Scale (100 contacts)

| Service | Cost/Month |
|---------|------------|
| Render Professional | $50 |
| ElevenLabs (500 min) | $1,500 |
| Twilio | $500 |
| **Total** | **~$2,050/month** |

**Revenue:** 100 contacts × $35/month = $3,500/month
**Profit:** $1,450/month (41% margin)

### Optimization Tips

1. **Use Batch Calling API** (ElevenLabs) for >50 calls/day
2. **Cache common responses** to reduce TTS costs
3. **Optimize call duration** (target 3-4 min instead of 5)
4. **Use Twilio's bulk pricing** for high volume

---

## Step 11: Backup and Disaster Recovery

### 11.1 Automated Backups

**Contacts and Memory:**

```bash
# Add to scheduler.py (runs daily at midnight)
def backup_data():
    import boto3
    s3 = boto3.client('s3')
    s3.upload_file('app/contacts.json', 'cerca-backups',
                   f'contacts_{datetime.now().strftime("%Y%m%d")}.json')
    s3.upload_file('app/memory.json', 'cerca-backups',
                   f'memory_{datetime.now().strftime("%Y%m%d")}.json')
```

### 11.2 Disaster Recovery Plan

**Service Outage:**
1. Render auto-restarts failed services
2. If Render is down → deploy to Heroku as backup (same code)
3. Update webhook URL in ElevenLabs

**Data Loss:**
1. Restore `contacts.json` from S3 backup
2. `memory.json` loss is non-critical (rebuilds over time)

**ElevenLabs Outage:**
- LLM cascading provides automatic failover
- If entire platform down → queue calls for later

---

## Step 12: Go-Live Checklist

Before announcing to real customers:

- [ ] All environment variables set correctly
- [ ] Webhook responds to test payloads
- [ ] Test call completes end-to-end
- [ ] WhatsApp arrives at correct number
- [ ] Memory persists between test calls
- [ ] Health check endpoint accessible
- [ ] Logs show no errors
- [ ] Scheduler triggers at correct times
- [ ] Monitoring alerts configured
- [ ] Backups running daily
- [ ] Documentation reviewed by team
- [ ] Legal consent forms prepared
- [ ] Privacy policy published
- [ ] Customer support plan ready

---

## Support

For deployment issues:

1. **Check Render logs first** (Dashboard → Logs)
2. **Review ElevenLabs dashboard** for call failures
3. **Test webhook manually** with curl
4. **Open issue on GitHub** with logs

---

## Next Steps

After successful deployment:

1. **Pilot Testing:** Run with 3-5 real families for 2 weeks
2. **Collect Feedback:** Daily check-ins with pilot users
3. **Iterate:** Fix issues, improve prompts
4. **Scale:** Add more contacts gradually
5. **Monitor:** Watch metrics closely

---

**Production Deployment Complete!**

Your Cerca instance is now running 24/7, ready to bring peace of mind to families across the diaspora.
