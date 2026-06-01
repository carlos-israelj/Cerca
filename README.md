# Cerca

> **Bridging the distance between migrant families and their elderly loved ones through voice AI**

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Conversational_AI-blueviolet)](https://elevenlabs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

</div>

---

## The Problem

**36 million Latin Americans live abroad**, many in the US and Europe, earning in USD/EUR while their elderly parents remain in their home countries. The distance creates a painful reality:

- **"Did mom take her blood pressure medication today?"**
- **"Is dad okay? He sounded sad yesterday"**
- **"I call every day, but the time difference makes it hard"**

Traditional solutions fail:
- **Apps require smartphones** and tech literacy that many elderly don't have
- **Caregivers are expensive** and not available in all regions
- **Daily phone calls** are emotionally taxing for busy migrants

**The emotional tax:** guilt, worry, and the constant fear that something could go wrong thousands of miles away.

---

## The Solution

**Cerca** (Spanish for "near" or "close by") is a warm, patient voice assistant that calls elderly people on their regular phone every day, provides companionship, gently reminds them about medication, and sends a daily wellness summary to their family via WhatsApp.

### Key Innovation

This isn't just another reminder app. It's **emotional infrastructure**:
- Works on **any phone** (landline or mobile) - no smartphone needed
- **Natural, patient conversations** in Latin American Spanish
- **Remembers previous conversations** for genuine continuity
- **Detects health concerns** and alerts family immediately
- **Respects dignity** - never patronizing, always respectful

---

## Why ElevenLabs?

Building a voice AI that elderly people actually *enjoy* talking to requires world-class conversational AI. Here's why ElevenLabs Conversational AI Platform was the only choice:

### 1. **Natural, Low-Latency Conversations**
- **Flash v2.5 TTS** delivers <100ms latency for real-time conversation
- **Claude Sonnet 4.5 native integration** provides empathetic, context-aware responses
- **Custom turn management** with `turn_eagerness: patient` gives elderly users time to think and respond

### 2. **Built for This Use Case**
- **`spelling_patience: auto`** handles medication names like "Losartán"
- **`soft_timeout_config`** fills thinking pauses with natural muletillas ("Déjeme ver...")
- **`silence_end_call_timeout`** of 40s respects slower conversation pace
- **`skip_turn` system tool** allows users to say "un momento" without the agent interrupting

### 3. **Safety and Reliability**
- **LLM Cascading** with automatic failover ensures calls never drop due to model issues
- **Custom Guardrails (Alpha)** provide independent medical advice blocking layer
- **Voicemail detection** with personalized messages
- **End-call tool** allows graceful conversation closure

### 4. **Privacy by Design**
- **`record_voice: false`** - transcripts only, no audio recording
- **`retention_days: 30`** - automatic data deletion
- Ready for **Zero Retention Mode** when needed for HIPAA compliance

### 5. **Stateful Conversations**
- **Dynamic variables** inject context (medication, topics, family name)
- **Data collection** extracts structured insights (mood, health concerns, medication compliance)
- **Memory between calls** via `conversation_initiation_client_data` creates genuine continuity

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Daily Wellness Call Cycle                    │
└─────────────────────────────────────────────────────────────────┘

    09:00 AM (Ecuador time)
         │
         ▼
    ┌─────────┐
    │Scheduler│ → Triggers daily call for María
    └─────────┘
         │
         ▼
    ┌─────────┐
    │ Caller  │ → Injects dynamic variables:
    └─────────┘    • elder_name: "María"
         │         • medications_today: "Losartán a las nueve..."
         │         • last_call_summary: "Yesterday mentioned knee pain"
         ▼
    ╔════════════════════╗
    ║  ElevenLabs Agent  ║ → Claude Sonnet 4.5
    ║   (Hosted Voice)   ║   Flash v2.5 TTS (0.9x speed)
    ╚════════════════════╝   Patient turn management
         │
         │  Via Twilio PSTN
         ▼
    📞 María's phone rings
         │
         │  5-min warm conversation:
         │  • "¿Cómo se siente hoy?"
         │  • Talks about her plants
         │  • Reminds: "¿Ya tomó su Losartán?"
         │  • Detects: "My knee still hurts"
         ▼
    Call ends → Analysis begins
         │
         ▼
    ┌──────────┐
    │ Webhook  │ ← post_call_transcription
    └──────────┘    • transcript_summary
         │          • data_collection_results:
         │            - tomo_medicamento: true
         │            - estado_animo: "tranquila"
         │            - preocupacion_salud: "knee pain"
         │            - alerta_urgente: false
         ▼
    Saves summary to memory.json (for next call)
         │
         ▼
    ┌──────────┐
    │  Notify  │ → Sends WhatsApp to Carlos (in USA):
    └──────────┘
         │         "Call completed with María
         ▼          • Medication taken: ✓ Yes
                    • Mood: calm
    Carlos receives • Health concern: knee pain
    WhatsApp on his
    phone in USA     Summary: She mentioned her plants are
                    blooming and asked about you..."
```

---

## Features

### For Elderly Users
- **No app required** - works on any phone (landline or mobile)
- **Natural conversation** in their language and dialect
- **Patient and respectful** - never rushed or patronizing
- **Remembers previous talks** - "Last time you mentioned your grandson..."
- **Medication reminders** without being annoying

### For Family Members
- **Daily WhatsApp summary** - peace of mind every morning
- **Urgent alerts** 🔴 - immediate notification if something serious is detected
- **No burden** - automated, reliable, consistent
- **Transparent** - see exactly what was discussed

### Technical Features
- **Timezone-aware scheduling** - calls at the right time in each user's location
- **Memory between calls** - stateful conversations that build relationships
- **HMAC webhook verification** - enterprise-grade security
- **Health concern detection** - structured data extraction from natural conversation
- **Graceful degradation** - handles voicemail, busy, no-answer scenarios

---

## Real-World Impact

### Target Market
- **60+ million** people in the Latin American diaspora (US, Spain, Italy)
- **High purchasing power** (USD/EUR income)
- **Emotional purchase** - peace of mind is priceless
- **Underserved market** - existing solutions require smartphones or local infrastructure

### Unit Economics
- **Cost:** ~$15/month (ElevenLabs + Twilio for daily 5-min calls)
- **Price:** $25-40/month (33-60% margin)
- **TAM:** 36M migrants × $35/month × 5% penetration = $630M annual opportunity

### Social Impact
- **Reduces loneliness** in elderly populations
- **Prevents medical non-compliance** (missed medications)
- **Early detection** of health issues
- **Reduces guilt and anxiety** in migrant families
- **Creates jobs** in voice AI and eldercare tech

---

## Quick Start

### Prerequisites
- Python 3.10+
- [ElevenLabs account](https://elevenlabs.io) with Conversational AI access
- [Twilio account](https://www.twilio.com) with phone number and WhatsApp
- `ngrok` for local webhook testing (development only)

### Installation

1. **Clone and install**
```bash
git clone https://github.com/carlos-israelj/Cerca.git
cd Cerca
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Set up ElevenLabs Agent**

Use the [ElevenLabs CLI](https://github.com/elevenlabs/elevenlabs-cli) for agent-as-code workflow:

```bash
npm install -g @elevenlabs/cli
elevenlabs auth login
elevenlabs agents init
elevenlabs agents add "Cerca" --template customer-service
```

Then configure using the detailed specs in `agent/agent_config.md`:
- **Prompt:** Use `agent/system_prompt.md` (optimized for eldercare)
- **LLM:** `claude-sonnet-4-5` with default cascading
- **TTS:** `eleven_flash_v2_5` at 0.9x speed, Spanish, warm voice
- **Timezone:** `America/Guayaquil` (critical for time awareness)
- **Turn management:** Patient mode with 15s turn timeout
- **System tools:** `end_call`, `voicemail_detection`, `skip_turn`
- **Data collection:** `tomo_medicamento`, `estado_animo`, `preocupacion_salud`, `alerta_urgente`
- **Privacy:** `record_voice: false`, `retention_days: 30`

4. **Configure contacts**

Edit `app/contacts.json` with real contact data:

```json
{
  "contacts": [{
    "id": "maria_001",
    "active": true,
    "elder_name": "María",
    "elder_phone": "+593991234567",
    "family_name": "Carlos",
    "family_whatsapp": "whatsapp:+11234567890",
    "timezone": "America/Guayaquil",
    "call_time": "09:00",
    "medications": [
      { "name": "Losartán", "time": "09:00", "note": "para la presión" }
    ],
    "topics": ["sus plantas", "su nieto Mateo", "el clima"],
    "notes": "Vive sola. Carlos vive en EE.UU."
  }]
}
```

5. **Test the system**

```bash
# Terminal 1: Start webhook
cd app
python webhook.py

# Terminal 2: Expose webhook (development)
ngrok http 8000

# Configure webhook URL in ElevenLabs dashboard:
# https://YOUR-NGROK-URL.ngrok.io/webhook/elevenlabs

# Terminal 3: Trigger a test call
cd app
python caller.py maria_001
```

6. **Run scheduler (production)**

```bash
cd app
python scheduler.py
# Keeps running, triggers daily calls automatically
```

---

## Project Structure

```
cerca/
├── README.md                  # this file
├── CLAUDE.md                  # technical architecture (comprehensive)
├── DEPLOYMENT.md              # production deployment guide
├── requirements.txt           # Python dependencies
├── .env.example               # environment variables template
│
├── agent/
│   ├── system_prompt.md       # agent personality and guardrails
│   └── agent_config.md        # ElevenLabs agent configuration spec
│
└── app/
    ├── contacts.json          # elderly contacts database
    ├── memory.json            # conversation history (generated at runtime)
    ├── store.py               # contact + memory management
    ├── caller.py              # outbound call trigger
    ├── notify.py              # WhatsApp notifications (Twilio)
    ├── webhook.py             # FastAPI webhook server
    └── scheduler.py           # daily call scheduler (APScheduler)
```

---

## Testing

### Manual End-to-End Test

1. Set `elder_phone` in `contacts.json` to your own number
2. Run `python caller.py maria_001`
3. Answer the call and have a conversation
4. Hang up
5. Verify you receive a WhatsApp summary

### Automated Testing (Recommended)

Use ElevenLabs testing framework to avoid calling real people:

```bash
elevenlabs agents test <agent_id>
```

**Test scenarios to cover:**
- Tool calling: Agent never gives medical advice (guardrail test)
- Voicemail detection works correctly
- `alerta_urgente: true` triggers red alert WhatsApp
- Conversation with slow responses (elderly simulation)
- First call (no memory) vs. subsequent call (with memory)
- Call initiation failure handling

See `CLAUDE.md` section 13 for comprehensive testing strategy.

---

## Security & Privacy

### Medical Safety
- **Transparent:** Agent identifies itself as an assistant, never as a person or doctor
- **No medical advice:** Guardrails block diagnosis, dosage, or treatment recommendations
- **Not emergency services:** Directs life-threatening situations to local emergency numbers
- **Alerts family:** Urgent health concerns trigger immediate WhatsApp to family

### Data Privacy
- **No voice recording:** `record_voice: false` - only transcripts stored
- **30-day retention:** Automatic data deletion
- **HIPAA-ready:** Zero Retention Mode available for enterprise
- **Webhook security:** HMAC signature verification on all callbacks
- **Encrypted transport:** HTTPS/TLS for all API communications

### Compliance Roadmap
- [x] GDPR-compliant data handling
- [x] Consent-based calling
- [ ] HIPAA BAA (for US healthcare market)
- [ ] Data localization for EU market

---

## Deployment

### Production Architecture (Render)

See `DEPLOYMENT.md` for detailed instructions. Summary:

- **Webhook service** (web): FastAPI app handling ElevenLabs callbacks and WhatsApp sending
- **Scheduler service** (worker): Background process for daily call triggering
- **Environment:** Managed secrets via Render environment variables
- **Scaling:** Horizontal scaling ready with stateless webhook design
- **Monitoring:** Health checks, logging, error tracking

### Cost at Scale

| Scale | Calls/Day | Monthly Cost | Revenue ($35/user) | Margin |
|-------|-----------|--------------|-------------------|--------|
| Pilot | 3 | $45 | $105 | 57% |
| Small | 50 | $750 | $1,750 | 57% |
| Medium | 500 | $7,500 | $17,500 | 57% |
| Large | 5,000 | $75,000 | $175,000 | 57% |

*Assumes 5-min calls at $0.10/min (ElevenLabs + Twilio)*

---

## Roadmap

### Phase 1: MVP (Current)
- [x] Daily wellness calls with medication reminders
- [x] WhatsApp summaries to family
- [x] Memory between calls
- [x] Urgent health alerts

### Phase 2: Enhanced Intelligence
- [ ] Sentiment analysis trends (mood tracking over time)
- [ ] Pronunciation dictionary for regional medications
- [ ] A/B testing framework (voice comparison, greeting optimization)
- [ ] Multi-language support (Portuguese for Brazil)

### Phase 3: Scale
- [ ] Batch calling API for 100+ daily calls
- [ ] Database backend (PostgreSQL) with PHI encryption
- [ ] Web dashboard for family portal
- [ ] Integration with local pharmacy APIs

### Phase 4: Ecosystem
- [ ] WhatsApp Business API for richer media
- [ ] Integration with health monitoring devices
- [ ] Caregiver marketplace integration
- [ ] Insurance partnerships

---

## Technical Highlights for ElevenLabs Team

This project showcases advanced usage of the ElevenLabs Conversational AI platform:

### Advanced Features Used
1. **Agent-as-Code workflow** via CLI for version control
2. **Dynamic variables** for personalized, context-rich conversations
3. **Data collection** for structured insights from unstructured conversation
4. **Custom guardrails** for safety-critical use case
5. **Stateful conversations** with memory management pattern
6. **System tools** (`end_call`, `voicemail_detection`, `skip_turn`)
7. **LLM cascading** for reliability
8. **Webhook signature verification** for security
9. **Privacy controls** (`record_voice: false`, short retention)
10. **Timezone-aware** prompt configuration

### Why This Matters
- **Real social impact:** Addresses genuine pain point for 36M+ people
- **Production-ready:** Not a demo, designed for actual deployment
- **Defensible moat:** Data (local medication names, cultural nuances) + distribution
- **Scalable:** Architecture handles 10 or 10,000 daily calls
- **Validated need:** Migrant families are desperate for this solution

---

## Contributing

This is a pilot project, but contributions are welcome:

1. **Regional adaptations:** Medication databases for different countries
2. **Language variants:** Mexican, Argentine, Caribbean Spanish
3. **Testing:** Add test scenarios for edge cases
4. **Documentation:** Improve setup guides

---

## License

MIT License - see [LICENSE](LICENSE) for details

---

## Acknowledgments

Built with:
- **[ElevenLabs Conversational AI](https://elevenlabs.io)** - The heart of empathetic voice interactions
- **[Twilio](https://www.twilio.com)** - Phone + WhatsApp infrastructure
- **[FastAPI](https://fastapi.tiangolo.com)** - Modern webhook server
- **[APScheduler](https://apscheduler.readthedocs.io)** - Reliable job scheduling

Special thanks to the ElevenLabs team for building a platform that makes dignified, patient conversations with elderly users actually possible.

---

## Contact

**Carlos Jiménez**
- GitHub: [@carlos-israelj](https://github.com/carlos-israelj)
- Project: [github.com/carlos-israelj/Cerca](https://github.com/carlos-israelj/Cerca)

---

<div align="center">
  <p><strong>Built for the ElevenLabs Ambassador Program</strong></p>
  <p>Demonstrating how voice AI can solve real human problems at scale</p>
</div>
