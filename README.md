# Cerca

Asistente de voz que hace llamadas telefónicas diarias, cálidas y breves a personas mayores para recordarles su medicación y acompañarlas, enviando un resumen automático por WhatsApp a sus familiares.

## Características

- Llamadas diarias programadas a personas mayores
- Recordatorio de medicación con calidez y paciencia
- Conversación natural sobre temas de interés
- Detección de alertas urgentes de salud
- Resumen automático por WhatsApp al familiar
- Memoria entre llamadas para continuidad

## Requisitos previos

- Python 3.10 o superior
- Cuenta en [ElevenLabs](https://elevenlabs.io) con agente configurado
- Cuenta en [Twilio](https://www.twilio.com) con número de teléfono y WhatsApp
- `ngrok` para desarrollo local (exponer webhook)

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/carlos-israelj/Cerca.git
cd Cerca
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copia `.env.example` a `.env` y completa con tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus claves reales:

```env
ELEVENLABS_API_KEY=sk_xxx
ELEVENLABS_AGENT_ID=agent_xxx
ELEVENLABS_AGENT_PHONE_NUMBER_ID=phnum_xxx
ELEVENLABS_WEBHOOK_SECRET=wsec_xxx

TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

FALLBACK_FAMILY_WHATSAPP=whatsapp:+1XXXXXXXXXX
```

### 4. Configurar el agente en ElevenLabs

Lee `agent/agent_config.md` para instrucciones detalladas. Resumen:

1. Instala la CLI de ElevenLabs: `npm install -g @elevenlabs/cli`
2. Autentica: `elevenlabs auth login`
3. Crea el agente usando la plantilla `customer-service`
4. Configura el prompt usando `agent/system_prompt.md`
5. Configura el webhook apuntando a tu dominio + `/webhook/elevenlabs`
6. Importa tu número de Twilio y anota los IDs

### 5. Configurar contactos

Edita `app/contacts.json` con los datos de las personas mayores a llamar:

```json
{
  "contacts": [
    {
      "id": "maria_001",
      "active": true,
      "elder_name": "María",
      "elder_phone": "+593991234567",
      "family_name": "Carlos",
      "family_whatsapp": "whatsapp:+11234567890",
      "timezone": "America/Guayaquil",
      "call_time": "09:00",
      "medications": [
        {
          "name": "Losartán",
          "time": "09:00",
          "note": "para la presión"
        }
      ],
      "topics": ["sus plantas", "su nieto Mateo", "el clima"],
      "notes": "Vive sola."
    }
  ]
}
```

## Uso

### Prueba manual (disparar una llamada)

```bash
cd app
python caller.py maria_001
```

Esto dispara inmediatamente una llamada al contacto especificado.

### Iniciar el webhook (desarrollo local)

En una terminal:

```bash
cd app
python webhook.py
```

En otra terminal, exponer con ngrok:

```bash
ngrok http 8000
```

Copia la URL de ngrok (ej: `https://abc123.ngrok.io`) y configúrala como webhook en ElevenLabs: `https://abc123.ngrok.io/webhook/elevenlabs`

### Programar llamadas diarias automáticas

```bash
cd app
python scheduler.py
```

Esto programa llamadas diarias para todos los contactos activos. El scheduler seguirá corriendo hasta que lo detengas con `Ctrl+C`.

## Estructura del proyecto

```
cerca/
├── README.md              # este archivo
├── CLAUDE.md              # documentación técnica completa
├── requirements.txt       # dependencias Python
├── .env.example           # plantilla de variables de entorno
├── agent/
│   ├── system_prompt.md   # prompt del agente para ElevenLabs
│   └── agent_config.md    # guía de configuración del agente
└── app/
    ├── contacts.json      # personas mayores a llamar
    ├── memory.json        # resúmenes de llamadas anteriores (generado)
    ├── store.py           # gestión de contactos y memoria
    ├── caller.py          # dispara llamadas salientes
    ├── notify.py          # envía WhatsApp vía Twilio
    ├── webhook.py         # recibe eventos post-llamada
    └── scheduler.py       # programa llamadas diarias
```

## Arquitectura

```
scheduler.py ──(hora programada)──► caller.py
                                      │
                                      ▼
                          ElevenLabs Agent (hosted)
                                      │
                                      ▼
                          📞 Persona mayor (PSTN)
                                      │
                                      ▼
                          webhook.py ◄── POST post_call_transcription
                              │
                              ▼
                          notify.py ──► 💬 WhatsApp al familiar
```

## Seguridad y privacidad

- El agente se presenta como asistente de voz, no como persona real
- NO da consejo médico (derivar al médico o familia)
- NO es línea de emergencias (pide llamar al 911 si hay riesgo vital)
- `record_voice: false` - solo guarda transcripción, no audio
- `retention_days: 30` - datos se eliminan automáticamente
- Verificación de firma HMAC en todos los webhooks

## Costos estimados

- Llamada de agente: ~USD 0.10/min
- Una llamada de ~5 min/día ≈ USD 15/mes (ElevenLabs + Twilio)
- Precio sugerido al cliente: USD 25-40/mes

## Testing

### Prueba de notificación WhatsApp

```bash
cd app
python notify.py +593991234567 "Prueba desde Cerca"
```

### Prueba end-to-end

1. Configura `elder_phone` con tu propio número
2. Ejecuta `python caller.py maria_001`
3. Atiende la llamada y conversa con el agente
4. Cuelga y verifica que llegue el WhatsApp de resumen

## Desarrollo

Para más detalles técnicos, consulta:
- `CLAUDE.md` - arquitectura, contratos de API, modelos de datos
- `agent/system_prompt.md` - personalidad y guardrails del agente
- `agent/agent_config.md` - configuración detallada del agente

## Soporte

Para problemas o preguntas:
1. Revisa `CLAUDE.md` para detalles técnicos
2. Verifica logs de ElevenLabs y Twilio
3. Asegúrate de que el webhook esté accesible públicamente

## Licencia

MIT
