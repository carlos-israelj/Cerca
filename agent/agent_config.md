# Configuración del agente en ElevenLabs

El agente se puede configurar de dos formas. Para Cerca usamos **agente como código**
(ElevenLabs CLI), porque deja la configuración versionada en el repo y editable por Claude Code,
en vez de hacer clics en el panel. El panel sigue sirviendo para inspeccionar y para enlazar la
telefonía.

> Los nombres de campo de este documento son los reales del esquema de la API
> (`conversation_config` / `platform_settings`). Respétalos al pie de la letra.

---

## 0. Agente como código (ElevenLabs CLI)

Requiere **Node.js ≥ 16**.

```bash
npm install -g @elevenlabs/cli
elevenlabs auth login                          # pega tu API key
elevenlabs agents init                         # crea la estructura del proyecto
elevenlabs agents add "Cerca" --template customer-service
```

La plantilla `customer-service` es buena base: prompts empáticos, temperatura baja (0.1) y
criterios de evaluación ya incluidos — encaja con una llamada de cuidado.

Estructura que genera la CLI:

```
agents.json            # registro central de agentes
tools.json             # registro de tools
tests.json             # registro de tests
agent_configs/         # config de cada agente (Cerca.json va aquí)
tool_configs/
test_configs/
```

Flujo de trabajo:

```bash
elevenlabs agents pull --agent "Cerca"         # baja la config actual al repo
# editas agent_configs/Cerca.json …
elevenlabs agents push --agent "Cerca" --dry-run   # previsualiza el diff
elevenlabs agents push --agent "Cerca"             # sube los cambios
elevenlabs agents test agent_xxxxxxxx              # corre los tests (sección 9)
```

> Si usas versioning, `--branch "<nombre>"` empuja a una rama concreta (ver sección 11).

---

## 1. Voz y modelo (TTS)

Dos opciones, decide según latencia vs calidez:

- **`eleven_flash_v2_5`** — ~75 ms, real-time. La opción segura para empezar.
- **`eleven_v3_conversational`** — entrega emocional y consciente del contexto, mismo precio
  aproximado (~USD 0.08/min). Más cálida, ligeramente más latencia. Vale la pena evaluarla para
  Cerca porque la calidez importa con una persona mayor. (Nota: v3 no preserva voces clonadas PVC.)

Recomendación: arranca con Flash v2.5; haz un experimento A/B (sección 11) contra v3 conversational
y mídelo con datos reales antes de decidir.

- **Idioma:** `es`. Voz de la librería con acento latinoamericano, tono cálido y maduro.
- **`speed`:** ~0.9 (rango 0.7–1.2). Un poco más lento que lo normal ayuda a la comprensión.
- **`timezone`:** **`America/Guayaquil`** — IMPORTANTE. Sin esto el agente no tiene noción de la
  fecha/hora actual y puede alucinar referencias temporales ("buenos días" de noche, "su medicación
  de hoy" sin saber qué día es). Se fija en el prompt del agente (`conversation_config.agent.prompt.timezone`).

### Números y pronunciación
Flash v2.5 **no normaliza números** por defecto. Tres caminos (puedes combinar):
- Escribir horas y dosis en palabras en los datos del contacto ("dos pastillas a las nueve").
- `text_normalisation_type: "elevenlabs"` (normaliza tras generar; añade algo de latencia).
- **Diccionario de pronunciación** (`pronunciation_dictionary_locators`) para nombres de medicamentos
  como "Losartán". Usa reglas tipo **alias** (los fonemas son solo para inglés).
- `spelling_patience: "auto"` para que el agente sea más paciente cuando se deletrean números o nombres.

---

## 2. LLM del agente (cerebro)

- **Usa Claude nativo: `claude-sonnet-4-5`.** Está integrado en la plataforma de agentes (no
  necesitas Speech Engine ni Custom LLM). Es de los mejores para tool-calling, que es lo que hace
  el agente al usar `voicemail_detection`, `end_call`, etc.
- **Backup LLM (cascading):** déjalo en **`default`**. Si Claude falla puntualmente, la plataforma
  reintenta con una secuencia de respaldo automática. `cascade_timeout_seconds` entre 2 y 15s.
- **NO uses Custom LLM** (Groq/Together/SambaNova/endpoint propio) para Cerca: desactiva el cascading
  (solo reintenta tu mismo endpoint) y añade infraestructura. Claude nativo da mejor calidad y el
  colchón de failover. Reconsiderar solo si el costo del LLM se volviera un problema serio a gran escala.

```json
{
  "conversation_config": {
    "agent": {
      "prompt": {
        "llm": "claude-sonnet-4-5",
        "backup_llm_config": { "type": "default" },
        "timezone": "America/Guayaquil"
      }
    }
  }
}
```

---

## 3. Prompt y primer mensaje

- **System prompt:** pega el contenido de `system_prompt.md` (está estructurado en
  `# Personality / # Goal / # Tone / # Guardrails`, el formato recomendado por ElevenLabs).
- **Primer mensaje (First message):**

  ```
  Hola {{elder_name}}, muy buenos días. Le habla Cerca, el asistente de voz que {{family_name}}
  preparó para acompañarle un ratito. ¿Cómo se siente hoy?
  ```

---

## 4. Flujo conversacional pensado para una persona mayor

Estos ajustes (`conversation_config.turn` y `conversation_config.tts`) hacen la diferencia entre
una llamada que atropella y una que acompaña:

| Campo                                | Valor sugerido | Por qué                                                            |
| ------------------------------------ | -------------- | ------------------------------------------------------------------ |
| `turn.turn_eagerness`                | `patient`      | El agente espera más antes de responder; no interrumpe.            |
| `turn.turn_timeout`                  | `~15` (seg)    | Da tiempo amplio a responder. (NO lo desactives.)                  |
| `turn.silence_end_call_timeout`      | `~40` (seg)    | Si hay silencio prolongado, cierra con dignidad en vez de colgar seco. |
| `turn.spelling_patience`             | `auto`         | Paciencia extra cuando se deletrean números/nombres (dosis, medicamentos). |
| `turn.soft_timeout_config`           | ver abajo      | Muletilla mientras el LLM piensa, para que no haya silencio incómodo. |
| `tts.speed`                          | `~0.9`         | Habla un poco más despacio.                                        |

`soft_timeout_config`:
```json
{
  "timeout_seconds": 3.0,
  "message": "Déjeme ver…",
  "use_llm_generated_message": false
}
```

- **Interrupciones:** habilitadas (que la persona pueda cortar al agente con naturalidad).
- **`skip_turn`** (system tool, sección 6): permite que el agente calle si la persona dice "déjeme
  pensar" o "un momento".

> No usamos el evento `agent_response_complete`: requiere desactivar `turn_timeout`, y aquí lo
> queremos largo, no apagado.

---

## 5. Análisis post-llamada → Data collection

En **Conversation Analysis → Data collection** (o en `platform_settings` vía CLI). El backend los
lee del webhook para armar el WhatsApp. Los nombres deben coincidir EXACTO:

| Campo                  | Tipo    | Instrucción para el analizador                                                                                                                                           |
| ---------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tomo_medicamento`     | Boolean | `true` si la persona confirmó que ya tomó su medicación de hoy; `false` si dijo que no o no quedó claro.                                                                  |
| `estado_animo`         | String  | Una o dos palabras sobre su ánimo general (p. ej.: animada, tranquila, triste, sola, confundida).                                                                         |
| `preocupacion_salud`   | String  | Síntoma, dolor o malestar que haya mencionado, descrito brevemente. Si no mencionó nada, responde `ninguna`.                                                              |
| `alerta_urgente`       | Boolean | `true` SOLO si mencionó algo que requiere atención pronta de la familia: caída, dolor de pecho, dificultad para respirar, confusión severa, o angustia grave. Si no, `false`. |

## 6. System tools (añadir explícitamente)

OJO: si el agente se crea por API/CLI, **`end_call` hay que añadirlo a mano** (el panel lo agrega
por defecto, la API no). Tools relevantes para Cerca:

| Tool                  | Para qué                                                                                  |
| --------------------- | ----------------------------------------------------------------------------------------- |
| `end_call`            | Terminar la llamada con gracia al despedirse. **Añadir manualmente.**                     |
| `voicemail_detection` | Detectar buzón de voz y dejar un recado (ver abajo).                                      |
| `skip_turn`           | Callar cuando la persona pide un momento.                                                 |

`voicemail_detection` admite un `voicemail_message` con variables dinámicas:
```json
{
  "system_tool_type": "voicemail_detection",
  "voicemail_message": "Hola {{elder_name}}, le llamaba Cerca de parte de {{family_name}} para saludarle. Le llamo más tardecito. Que tenga buen día."
}
```
Si la llamada cae en buzón, ElevenLabs **no** manda `call_initiation_failure` (la llamada sí se
inició); por eso el recado se maneja aquí.

## 7. Guardrails (seguridad en profundidad)

Dos capas, no una:
1. **En el prompt:** la sección `# Guardrails` de `system_prompt.md` (sin consejo médico, no hacerse
   pasar por persona/médico, no es línea de emergencias).
2. **Custom Guardrail independiente (Alpha):** una regla evaluada por un LLM aparte que **bloquea
   consejo médico, diagnósticos y dosis**. Es defensa redundante: si el prompt fallara, el guardrail
   ataja. Configúralo con una regla tipo healthcare ("block medical advice / diagnosis / dosage").

## 8. Privacidad (como código)

En `platform_settings.privacy`:

| Campo                  | Valor para el piloto | Por qué                                                            |
| ---------------------- | -------------------- | ------------------------------------------------------------------ |
| `record_voice`         | `false`              | Guarda la transcripción pero NO el audio. El audio de una persona mayor hablando de su salud es lo más sensible; el resumen de texto basta. |
| `retention_days`       | `30` (o menos)       | Por defecto son 2 años. Para datos de salud de un piloto, agresivamente corto. |

```json
{
  "platform_settings": {
    "privacy": { "record_voice": false, "retention_days": 30 }
  }
}
```

> **Ruta enterprise/HIPAA** (no para el piloto): `zero_retention_mode: true` + redacción de entidades.
> ZRM no almacena nada y obliga a recuperar todo vía post-call webhook (que ya tienes). Es la única
> vía hacia HIPAA real si algún día manejas familias de la diáspora en EE.UU. (requiere BAA).

## 9. Testing automatizado (sin llamar a nadie real)

No puedes andar haciendo llamadas de prueba a una persona mayor. Usa el framework de testing
(`elevenlabs agents test <id>` o el endpoint de simulación):

- **Tool Call Testing:** verifica que el agente llame a `voicemail_detection` cuando toca, y que
  **nunca** dé consejo médico. Prueba casos adversariales ("¿qué hago si me duele el pecho?") y
  confirma que el guardrail ataja.
- **Simulation Testing (alpha):** un usuario simulado (ej. "persona mayor con audición reducida que
  responde despacio") corre una conversación completa de varios turnos; evalúas si llegó al objetivo.
  Soporta **tool mocking**, así que pruebas sin disparar WhatsApp real.
- **Scenario Testing:** evalúa un siguiente turno contra criterios en lenguaje natural.

Casos mínimos a cubrir: medicación tomada/no tomada; `alerta_urgente` true; intento de sacarle
consejo médico (debe rehusar); persona que pide "un momento" (`skip_turn`); buzón de voz.

## 10. Evaluación

En **Evaluation criteria**:

| Criterio          | Definición                                                                            |
| ----------------- | ------------------------------------------------------------------------------------- |
| `llamada_exitosa` | La llamada logró saludar, conversar brevemente y abordar el tema de la medicación.    |

## 11. Telefonía

- Importa tu número de Twilio en **Phone numbers** y enlázalo al agente.
- Anota el `agent_id` y el `agent_phone_number_id`: van en el `.env`.

## 12. Webhook post-llamada

- En **Agents settings → Post-call webhook**, apunta a `https://TU-DOMINIO/webhook/elevenlabs`
  (en local usa `ngrok`).
- Guarda el **webhook secret** → `ELEVENLABS_WEBHOOK_SECRET`.
- Activa `post_call_transcription`. El `call_initiation_failure` te avisa cuando no contestan
  (ocupado/no-answer/unknown) — recuerda: NO se envía si cae en buzón.

## 13. Versioning y Experiments (post-piloto, no para el MVP)

Cuando tengas volumen, `enable_versioning` permite ramas y A/B testing con tráfico real: probar dos
saludos, dos voces (Flash vs v3) o dos niveles de calidez y medir cuál deja más tranquila a la
familia (CSAT, duración, `llamada_exitosa`). Empieza con 5–10% de tráfico en la variante. Encaja
con el mandato de validar con datos, pero no toques esto hasta pasar el piloto.
