"""
Webhook module: recibe y procesa eventos post-llamada de ElevenLabs.
"""
import os
from fastapi import FastAPI, Request, HTTPException
from elevenlabs import ElevenLabs
from dotenv import load_dotenv
from store import get_contact, save_last_summary
from notify import send_whatsapp

# Cargar variables de entorno
load_dotenv()

# Configuración
ELEVENLABS_WEBHOOK_SECRET = os.getenv("ELEVENLABS_WEBHOOK_SECRET")
FALLBACK_FAMILY_WHATSAPP = os.getenv("FALLBACK_FAMILY_WHATSAPP")

# Crear cliente de ElevenLabs para verificación de firma
eleven = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Crear app FastAPI
app = FastAPI(title="Cerca Webhook")


@app.get("/health")
async def health():
    """Endpoint de health check."""
    return {"status": "ok", "service": "cerca-webhook"}


@app.post("/webhook/elevenlabs")
async def elevenlabs_webhook(request: Request):
    """
    Webhook que recibe eventos post-llamada de ElevenLabs.
    Verifica la firma, procesa el evento y devuelve 200 siempre.
    """
    try:
        # Leer el cuerpo de la petición
        payload = await request.body()
        sig_header = request.headers.get("elevenlabs-signature", "")

        # Verificar firma usando el SDK de ElevenLabs
        try:
            event = eleven.webhooks.construct_event(
                rawBody=payload.decode("utf-8"),
                sig_header=sig_header,
                secret=ELEVENLABS_WEBHOOK_SECRET,
            )
        except Exception as e:
            print(f"Error verificando firma del webhook: {e}")
            # Devolver 200 de todos modos para no desactivar el webhook
            return {"status": "signature_error"}

        # Enrutar según el tipo de evento
        event_type = event.get("type", "")
        data = event.get("data", {})

        if event_type == "post_call_transcription":
            handle_transcription(data)
        elif event_type == "call_initiation_failure":
            handle_call_failure(data)
        elif event_type == "post_call_audio":
            # No procesamos audio en este MVP
            print("Evento post_call_audio recibido (no procesado)")
        else:
            print(f"Tipo de evento desconocido: {event_type}")

        # SIEMPRE devolver 200 para evitar que el webhook se auto-deshabilite
        return {"status": "ok"}

    except Exception as e:
        print(f"Error procesando webhook: {e}")
        # Incluso en caso de error, devolver 200
        return {"status": "error", "message": str(e)}


def handle_transcription(data: dict) -> None:
    """
    Procesa el evento post_call_transcription:
    1. Recupera contact_id de las variables dinámicas
    2. Lee el resumen y los campos de data collection
    3. Guarda el resumen en memoria
    4. Envía WhatsApp a la familia (normal o urgente)
    """
    try:
        # Recuperar contact_id de las dynamic variables
        dynamic_vars = data.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
        contact_id = dynamic_vars.get("contact_id")

        if not contact_id:
            print("Error: contact_id no encontrado en las dynamic variables")
            return

        # Obtener datos del contacto
        contact = get_contact(contact_id)
        if not contact:
            print(f"Error: Contacto '{contact_id}' no encontrado")
            return

        # Extraer análisis de la llamada
        analysis = data.get("analysis", {})
        transcript_summary = analysis.get("transcript_summary", "Sin resumen disponible")

        # Guardar resumen en memoria para la próxima llamada
        save_last_summary(contact_id, transcript_summary)

        # Extraer campos de data collection (leer .value de forma defensiva)
        data_collection = analysis.get("data_collection_results", {})

        tomo_medicamento = data_collection.get("tomo_medicamento", {}).get("value")
        estado_animo = data_collection.get("estado_animo", {}).get("value", "no especificado")
        preocupacion_salud = data_collection.get("preocupacion_salud", {}).get("value", "ninguna")
        alerta_urgente = data_collection.get("alerta_urgente", {}).get("value", False)

        # Armar mensaje de WhatsApp
        elder_name = contact.get("elder_name", "la persona mayor")
        family_name = contact.get("family_name", "familiar")

        if alerta_urgente:
            # Mensaje urgente
            message = f"""🔴 ALERTA URGENTE - {elder_name}

{family_name}, acabo de hablar con {elder_name} y mencionó algo que requiere atención inmediata.

Preocupación de salud: {preocupacion_salud}

Por favor, comunícate con {elder_name} lo antes posible.

Resumen de la llamada:
{transcript_summary}

— Cerca"""
        else:
            # Mensaje normal
            medicamento_status = "✓ Sí" if tomo_medicamento else "✗ No" if tomo_medicamento is False else "No preguntado"

            message = f"""Llamada completada con {elder_name}

Hola {family_name}, acabo de hablar con {elder_name}. Aquí está el resumen:

• Medicación tomada: {medicamento_status}
• Estado de ánimo: {estado_animo}
• Preocupación de salud: {preocupacion_salud}

Resumen:
{transcript_summary}

— Cerca"""

        # Enviar WhatsApp a la familia
        family_whatsapp = contact.get("family_whatsapp", FALLBACK_FAMILY_WHATSAPP)
        if family_whatsapp:
            send_whatsapp(family_whatsapp, message)
        else:
            print(f"Error: No hay número de WhatsApp configurado para {contact_id}")

        print(f"Procesamiento completado para {contact_id}")

    except Exception as e:
        print(f"Error en handle_transcription: {e}")


def handle_call_failure(data: dict) -> None:
    """
    Procesa el evento call_initiation_failure:
    Avisa a la familia que la llamada no se completó.
    """
    try:
        # Recuperar contact_id de las dynamic variables
        dynamic_vars = data.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
        contact_id = dynamic_vars.get("contact_id")

        if not contact_id:
            print("Error: contact_id no encontrado en call_initiation_failure")
            return

        # Obtener datos del contacto
        contact = get_contact(contact_id)
        if not contact:
            print(f"Error: Contacto '{contact_id}' no encontrado")
            return

        # Extraer razón del fallo
        failure_reason = data.get("failure_reason", "desconocido")
        elder_name = contact.get("elder_name", "la persona mayor")
        family_name = contact.get("family_name", "familiar")

        # Armar mensaje
        message = f"""Llamada no completada - {elder_name}

Hola {family_name}, no pude completar la llamada con {elder_name}.

Razón: {failure_reason}

Volveré a intentar más tarde.

— Cerca"""

        # Enviar WhatsApp a la familia
        family_whatsapp = contact.get("family_whatsapp", FALLBACK_FAMILY_WHATSAPP)
        if family_whatsapp:
            send_whatsapp(family_whatsapp, message)
        else:
            print(f"Error: No hay número de WhatsApp configurado para {contact_id}")

        print(f"Call failure notificado para {contact_id}")

    except Exception as e:
        print(f"Error en handle_call_failure: {e}")


if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor webhook en http://localhost:8000")
    print("Endpoints disponibles:")
    print("  - GET  /health")
    print("  - POST /webhook/elevenlabs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
