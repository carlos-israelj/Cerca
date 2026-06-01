"""
Caller module: dispara llamadas salientes a través de ElevenLabs.
"""
import os
import sys
import requests
from dotenv import load_dotenv
from store import get_contact, medications_text, topics_text, get_last_summary

# Cargar variables de entorno
load_dotenv()

# Configuración de ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
ELEVENLABS_AGENT_PHONE_NUMBER_ID = os.getenv("ELEVENLABS_AGENT_PHONE_NUMBER_ID")

# Endpoint de llamadas salientes
OUTBOUND_CALL_URL = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"


def place_call(contact_id: str) -> bool:
    """
    Dispara una llamada saliente al contacto especificado.

    Args:
        contact_id: ID del contacto a llamar (ej: "maria_001")

    Returns:
        True si la llamada se disparó exitosamente, False en caso de error
    """
    try:
        # Validar configuración
        if not all([ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, ELEVENLABS_AGENT_PHONE_NUMBER_ID]):
            print("Error: Configuración de ElevenLabs incompleta en .env")
            return False

        # Obtener datos del contacto
        contact = get_contact(contact_id)
        if not contact:
            print(f"Error: Contacto '{contact_id}' no encontrado")
            return False

        # Verificar que el contacto esté activo
        if not contact.get("active", False):
            print(f"Error: Contacto '{contact_id}' está inactivo")
            return False

        # Preparar variables dinámicas para el agente
        dynamic_variables = {
            "contact_id": contact_id,
            "elder_name": contact.get("elder_name", ""),
            "family_name": contact.get("family_name", ""),
            "medications_today": medications_text(contact),
            "topics": topics_text(contact),
            "last_call_summary": get_last_summary(contact_id)
        }

        # Construir payload de la llamada
        payload = {
            "agent_id": ELEVENLABS_AGENT_ID,
            "agent_phone_number_id": ELEVENLABS_AGENT_PHONE_NUMBER_ID,
            "to_number": contact.get("elder_phone"),
            "conversation_initiation_client_data": {
                "dynamic_variables": dynamic_variables
            }
        }

        # Headers
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        # Realizar llamada al API
        print(f"Disparando llamada a {contact.get('elder_name')} ({contact.get('elder_phone')})...")
        response = requests.post(OUTBOUND_CALL_URL, json=payload, headers=headers)

        # Verificar respuesta
        if response.status_code in [200, 201]:
            print(f"✓ Llamada disparada exitosamente para {contact_id}")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Error al disparar llamada: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"Error inesperado al disparar llamada para {contact_id}: {e}")
        return False


if __name__ == "__main__":
    # CLI: python caller.py <contact_id>
    if len(sys.argv) < 2:
        print("Uso: python caller.py <contact_id>")
        print("Ejemplo: python caller.py maria_001")
        sys.exit(1)

    contact_id = sys.argv[1]
    success = place_call(contact_id)
    sys.exit(0 if success else 1)
