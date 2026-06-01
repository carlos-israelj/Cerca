# CLAUDE.md — Cerca

> Coloca este archivo en la raíz del repositorio. Claude Code lo lee como contexto del proyecto.
> Es la fuente de verdad de arquitectura, dependencias, contratos de API y orden de construcción.

---

## 1. Qué es el proyecto

**Cerca** hace llamadas telefónicas diarias, cálidas y breves a una persona mayor (recordatorio de
medicación + visita de bienestar) y envía un resumen automático por WhatsApp a su familiar que vive
lejos.

- **Quién recibe la llamada:** la persona mayor, en su teléfono normal. No necesita celular, app ni internet.
- **Quién paga:** el hijo/a migrante (diáspora, ingresos en USD/EUR). Compra emocional.
- **Qué compra:** tranquilidad — un WhatsApp diario que dice cómo estuvo la llamada.
- **Foso defensible:** no es la voz (commodity), sino la data local, la distribución y la confianza/acento regional.

**Regla de negocio antes que código:** la incógnita real es si el hijo/a paga. Hay que vender un
piloto de 2 semanas a 3–5 familias reales antes de escalar. Construir poco, validar rápido.

---

## 2. Objetivo de este código (MVP)

Implementar el ciclo completo de una llamada:

1. Programar y disparar una llamada saliente diaria por contacto.
2. Que un agente de voz (ElevenLabs) converse en español con la persona mayor.
3. Al colgar, recibir el análisis de la llamada por webhook.
4. Enviar un resumen por WhatsApp al familiar (con alerta urgente si aplica).
5. Recordar la conversación anterior en la siguiente llamada (memoria entre llamadas).

No incluye (todavía): base de datos, panel web, multi-tenant, facturación.

---

## 3. Arquitectura

ElevenAgents coordina 4 componentes: reconocimiento de voz (ASR), el LLM, TTS de baja latencia, y un
modelo propietario de turnos. Usamos la plataforma **hosted** con **Claude Sonnet 4.5 como LLM nativo**
(integrado en la plataforma; no requiere Speech Engine ni Custom LLM).

```
scheduler.py ──(a la hora de cada contacto, en su zona horaria)──► caller.py
                                                                     │  POST /v1/convai/twilio/outbound-call
                                                                     │  (inyecta dynamic_variables del contacto)
                                                                     ▼
                                                          ElevenLabs Agent (hosted)
                                                                     │  llama vía Twilio
                                                                     ▼
                                                          📞 persona mayor (PSTN)
                                                                     │  al colgar: análisis + data collection
                                                                     ▼
                                              webhook.py  ◄── POST post_call_transcription
                                                 │  1. verifica firma HMAC (SDK)
                                                 │  2. lee transcript_summary + data_collection_results
                                                 │  3. guarda el resumen en memory.json (memoria)
                                                 │  4. arma el mensaje (normal o 🔴 urgente)
                                                 ▼
                                              notify.py ──► 💬 WhatsApp al familiar (Twilio)
```

### Decisión: LLM nativo (Claude) vs Custom LLM
- **Claude Sonnet 4.5 nativo (lo que usamos):** integrado en la plataforma de agentes. Excelente para
  tool-calling y conserva el **LLM cascading** (failover automático a modelos de respaldo si Claude
  falla puntualmente). Cero infraestructura propia.
- **Custom LLM (Groq/Together/SambaNova/endpoint propio):** descartado para Cerca. Desactiva el
  cascading (solo reintenta tu mismo endpoint) y añade infraestructura. Reconsiderar solo si el costo
  del LLM se volviera un problema serio a gran escala.
- **Speech Engine** (traer tu propio LLM y lógica vía WebSocket) tampoco es necesario: Claude ya está
  disponible de forma nativa.

---

## 4. Stack y dependencias

- **Lenguaje:** Python 3.10+ (usa `zoneinfo` de la stdlib).
- **Web/webhook:** `fastapi`, `uvicorn[standard]`.
- **HTTP saliente:** `requests`.
- **Config:** `python-dotenv`.
- **ElevenLabs SDK:** `elevenlabs` (se usa para verificar la firma del webhook con `construct_event`).
- **WhatsApp/telefonía:** `twilio`.
- **Programación de llamadas:** `apscheduler`.

`requirements.txt`:
```
fastapi
uvicorn[standard]
requests
python-dotenv
elevenlabs
twilio
apscheduler
```

**Servicios externos:** cuenta ElevenLabs (Agents Platform), Twilio (número de voz + WhatsApp),
`ngrok` solo en desarrollo para exponer el webhook.

---

## 5. Estructura del proyecto

```
cerca/
├── CLAUDE.md               # este archivo
├── README.md               # puesta en marcha resumida
├── requirements.txt
├── .env.example            # plantilla de variables de entorno
├── agent/
│   ├── system_prompt.md    # prompt del agente (se pega en ElevenLabs)
│   └── agent_config.md     # voz, modelo, variables, data collection, webhook
└── app/
    ├── contacts.json       # personas mayores: teléfono, medicación, temas, WhatsApp familiar
    ├── memory.json         # generado en runtime: resumen de la última llamada por contacto
    ├── store.py            # carga de contactos + variables + memoria entre llamadas
    ├── caller.py           # dispara la llamada saliente
    ├── notify.py           # envía el WhatsApp
    ├── webhook.py          # recibe el resultado, valida, guarda memoria, avisa a la familia
    └── scheduler.py        # programa la llamada diaria de cada contacto
```

---

## 6. Modelos de datos

### `app/contacts.json`
```json
{
  "contacts": [
    {
      "id": "maria_001",
      "active": true,
      "elder_name": "María",
      "elder_phone": "+59399XXXXXXX",
      "family_name": "Carlos",
      "family_whatsapp": "whatsapp:+1XXXXXXXXXX",
      "timezone": "America/Guayaquil",
      "call_time": "09:00",
      "medications": [
        { "name": "Losartán", "time": "09:00", "note": "para la presión" }
      ],
      "topics": ["sus plantas", "su nieto Mateo", "el clima en Cuenca"],
      "notes": "Vive sola. Carlos vive en EE.UU."
    }
  ]
}
```

### `app/memory.json` (runtime, no se versiona)
```json
{
  "maria_001": { "last_summary": "Ayer mencionó que le dolía la rodilla." }
}
```

---

## 7. Variables de entorno (`.env`)

```
ELEVENLABS_API_KEY=sk_xxx
ELEVENLABS_AGENT_ID=agent_xxx
ELEVENLABS_AGENT_PHONE_NUMBER_ID=phnum_xxx
ELEVENLABS_WEBHOOK_SECRET=wsec_xxx

TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

FALLBACK_FAMILY_WHATSAPP=whatsapp:+1XXXXXXXXXX   # opcional
```

---

## 8. Configuración del agente (como código, vía ElevenLabs CLI)

El detalle vive en `agent/agent_config.md`. Resumen para tener a mano:

- **Agente como código:** se gestiona con la **ElevenLabs CLI** (Node ≥16): `elevenlabs agents
  init / pull / push / test`. La config queda versionada en `agent_configs/Cerca.json`. El panel
  solo se usa para inspeccionar y enlazar la telefonía.
- **LLM:** `claude-sonnet-4-5` nativo, con `backup_llm_config: default` (cascading on).
- **TTS:** Flash v2.5 para empezar (evaluar `eleven_v3_conversational` por calidez). Idioma `es`,
  voz latinoamericana cálida, `speed` ~0.9.
- **`timezone: America/Guayaquil`** en el prompt del agente — sin esto el agente no sabe la fecha/hora
  y aluciná referencias temporales.
- **Flujo para mayores:** `turn_eagerness: patient`, `turn_timeout` ~15s, `silence_end_call_timeout`
  ~40s, `spelling_patience: auto`, `soft_timeout_config` con muletilla, interrupciones on, `skip_turn`.
- **System tools:** `end_call` (¡añadir manualmente si se crea por API/CLI!), `voicemail_detection`
  (con `voicemail_message` dinámico), `skip_turn`.
- **Variables dinámicas** (las envía `caller.py`): `contact_id`, `elder_name`, `family_name`,
  `medications_today`, `topics`, `last_call_summary`.
- **Data collection** (nombres EXACTOS; `webhook.py` los lee): `tomo_medicamento` (Boolean),
  `estado_animo` (String), `preocupacion_salud` (String), `alerta_urgente` (Boolean).
- **Evaluación:** `llamada_exitosa`.
- **Guardrail independiente** (Alpha) que bloquea consejo médico/diagnóstico/dosis — defensa redundante
  además del prompt.
- **Privacidad:** `record_voice: false`, `retention_days: 30`.
- **Telefonía:** importar número Twilio → anotar `agent_phone_number_id`.
- **Webhook post-llamada:** apuntar a `https://TU-DOMINIO/webhook/elevenlabs`, guardar el secret.

---

## 9. Contratos de integración (autoritativo — respetar al implementar)

### Llamada saliente
```
POST https://api.elevenlabs.io/v1/convai/twilio/outbound-call
Header: xi-api-key: <ELEVENLABS_API_KEY>
Body: {
  "agent_id": "...",
  "agent_phone_number_id": "...",
  "to_number": "+593...",
  "conversation_initiation_client_data": {
    "dynamic_variables": { "contact_id": "...", "elder_name": "...", ... }
  }
}
```
Las `dynamic_variables` se sustituyen en el prompt como `{{nombre_variable}}` y **regresan** en el
webhook dentro de `data.conversation_initiation_client_data.dynamic_variables` (así recuperamos `contact_id`).

### Webhook post-llamada
- Tipos: `post_call_transcription` (el que usamos), `call_initiation_failure` (no contestó/ocupado),
  `post_call_audio` (audio base64, no usado).
- Estructura de `post_call_transcription`:
  - `type`, `event_timestamp`, `data`.
  - `data.transcript`, `data.metadata`, `data.conversation_initiation_client_data.dynamic_variables`.
  - `data.analysis.transcript_summary` (string).
  - `data.analysis.data_collection_results` → por campo: `{ "<campo>": { "value": ... } }` (leer `.value` de forma defensiva).
  - `data.analysis.evaluation_criteria_results`, `data.analysis.call_successful`.
- Debe devolver **200** siempre que se reciba (aunque el procesamiento interno falle), para evitar que
  el webhook se auto-deshabilite.

### Verificación de firma (NO hacer HMAC a mano)
Usar el SDK de ElevenLabs. Header `elevenlabs-signature`. `construct_event` valida firma + timestamp y
devuelve un **dict**:
```python
event = eleven.webhooks.construct_event(
    rawBody=payload.decode("utf-8"),
    sig_header=request.headers.get("elevenlabs-signature"),
    secret=WEBHOOK_SECRET,
)
```
Opcional adicional: whitelist de IPs de egreso de ElevenLabs en el firewall.

### Memoria entre llamadas (patrón "stateful conversations")
1. `webhook.py` guarda `transcript_summary` en `memory.json` por `contact_id`.
2. `caller.py` lo recupera y lo envía como variable `last_call_summary` en la siguiente llamada.
3. El system prompt la usa para retomar con naturalidad la conversación anterior.

---

## 10. Especificación por módulo

- **`store.py`**
  - `load_contacts()`, `get_contact(id)`.
  - `medications_text(contact)` → frase legible de medicación.
  - `topics_text(contact)` → temas separados por comas.
  - `get_last_summary(id)` / `save_last_summary(id, summary)` → leen/escriben `memory.json` de forma
    tolerante a errores (archivo inexistente o JSON corrupto → no romper).

- **`caller.py`**
  - `place_call(contact_id)`: arma el body y hace POST al endpoint outbound. Incluye
    `last_call_summary` (o un texto por defecto si es la primera llamada). CLI: `python caller.py <id>`.

- **`notify.py`**
  - `send_whatsapp(to_number, body)`: envía vía Twilio. Acepta el número con o sin prefijo `whatsapp:`.

- **`webhook.py`** (FastAPI)
  - `POST /webhook/elevenlabs`: verifica firma → enruta por `type`. Devuelve 200 siempre.
  - `handle_transcription(data)`: recupera `contact_id` de las dynamic variables, lee summary +
    campos de data collection, **guarda el summary en memoria**, arma mensaje normal o 🔴 urgente
    (según `alerta_urgente`) y lo envía por WhatsApp.
  - `handle_call_failure(data)`: avisa a la familia que la llamada no se completó.
  - `GET /health`.

- **`scheduler.py`** (APScheduler `BlockingScheduler`)
  - Programa un `CronTrigger` diario por contacto activo, en su `timezone`. CLI: `python scheduler.py`.
  - Alternativa: cron del sistema llamando `python caller.py <id>` a la hora deseada.

---

## 11. Requisitos de seguridad (obligatorios, no negociables)

Implementar y mantener a lo largo de todo el código y el prompt:

- **Transparencia:** el agente se presenta como asistente de voz de parte de la familia. No se hace
  pasar por persona ni por médico.
- **Sin consejo médico:** solo recordatorios, compañía y acompañamiento. Ante dudas médicas, derivar
  al médico o a la familia. **Defensa en profundidad:** además de la regla en el prompt (`# Guardrails`),
  configurar un **Custom Guardrail independiente** (Alpha) que bloquee consejo médico/diagnóstico/dosis,
  por si el prompt fallara.
- **No es línea de emergencias:** si hay riesgo vital, el agente pide colgar y llamar a emergencias;
  la familia recibe alerta 🔴 inmediata por WhatsApp (campo `alerta_urgente`).
- **Privacidad como código:** `record_voice: false` (guardar transcripción, NO audio) y
  `retention_days: 30`. El audio de una persona mayor hablando de su salud es lo más sensible y no lo
  necesitamos. Ruta enterprise/HIPAA (futuro): Zero Retention Mode + redacción de entidades + BAA.
- **Consentimiento:** consentimiento para llamar y grabar antes de operar.

---

## 12. Orden de construcción (tareas para Claude Code)

1. Scaffold del repo, `requirements.txt`, `.env.example`, instalar dependencias.
2. `store.py` + `contacts.json` (con un contacto de prueba apuntando a TU propio teléfono).
3. `caller.py` + prueba manual: `python caller.py maria_001` y verificar que suena la llamada.
4. `webhook.py` + `notify.py`; exponer con `ngrok`; configurar el webhook en ElevenLabs.
5. Memoria entre llamadas (`get/save_last_summary` + variable `last_call_summary` + uso en el prompt).
6. `scheduler.py` para la llamada diaria automática.
7. Configurar el Custom Guardrail (anti-consejo-médico) y escribir tests automatizados (tool-call +
   simulation con mocking) vía `elevenlabs agents test`, para validar seguridad sin llamar a nadie real.
8. Pulido: logging consistente, manejo de errores, idempotencia del webhook (deduplicar por `conversation_id`).

---

## 13. Pruebas

- **Extremo a extremo (manual):** `elder_phone` = tu número; `python caller.py maria_001`; atender,
  conversar, colgar; confirmar que llega el WhatsApp de resumen.
- **Pruebas automatizadas (sin llamar a nadie real):** usar el framework de testing de ElevenLabs vía
  `elevenlabs agents test <id>`. **Tool Call Testing** para verificar que el agente nunca dé consejo
  médico y que llame a `voicemail_detection` cuando toca; **Simulation Testing** (con tool mocking)
  para correr conversaciones multi-turno con un usuario simulado (p. ej. persona mayor que responde
  despacio) sin disparar WhatsApp real.
- **Webhook local:** usar la simulación de ElevenLabs, o enviar un payload de ejemplo a
  `/webhook/elevenlabs`. La firma es obligatoria en producción.
- **Casos a cubrir:** medicación tomada / no tomada, `alerta_urgente` true (debe disparar 🔴), llamada
  no contestada (`call_initiation_failure`), primera llamada (sin memoria) vs llamada con memoria.

---

## 14. Costos (orden de magnitud)

- Llamada de agente: ~USD 0.10/min. TTS: 1 crédito por carácter. Tier gratis: ~10k caracteres/mes.
- Una llamada de ~5 min/día ≈ ~USD 15/mes entre ElevenLabs y Twilio. Precio sugerido al cliente: USD 25–40/mes.

---

## 15. Restricciones conocidas y caminos a futuro

- **Flash v2.5 no normaliza números** por defecto: escribir horas y dosis en palabras ("dos pastillas
  a las nueve") en los datos del contacto; o usar `text_normalisation_type: "elevenlabs"`; o un
  diccionario de pronunciación (alias) para medicamentos como "Losartán". Alternativa de voz más cálida:
  `eleven_v3_conversational`.
- **WhatsApp/SMS nativos en ElevenLabs** (evolución post-piloto, NO cambio del MVP): la plataforma
  puede importar la cuenta de WhatsApp Business y mandar mensajes con una "Send Message" tool, o
  responder por SMS importando un número Twilio. Eventualmente podría reemplazar `notify.py`. WhatsApp
  iniciado por el negocio igual requiere **plantillas aprobadas por Meta**; SMS nativo es el Plan B
  sin esa fricción.
- **WhatsApp iniciado por el negocio** (resumen diario) requiere **plantillas aprobadas por Meta** en
  Twilio antes de operar fuera del sandbox.
- **Salud + diáspora en EE.UU.:** el cumplimiento tipo HIPAA en ElevenLabs requiere firmar un BAA con su
  equipo comercial.
- **`memory.json` y `contacts.json`** sirven para el piloto; en producción → base de datos + cifrado de
  datos de salud.
- **Escalar a decenas/cientos de llamadas:** usar la API de **Batch calls** de ElevenLabs en lugar de
  disparar el endpoint outbound uno por uno.

---

## 16. Convenciones para Claude Code

- Mantener este archivo actualizado cuando cambie la arquitectura o los contratos de API.
- Respetar los **nombres exactos** de los campos de data collection y de las variables dinámicas: el
  prompt del agente y el código dependen de que coincidan.
- Nunca registrar (log) ni exponer datos de salud o números completos en texto plano.
- Para detalles vigentes de Claude Code, consultar su documentación oficial:
  https://docs.claude.com/en/docs/claude-code/overview
