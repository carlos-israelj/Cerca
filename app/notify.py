"""
Notify module: envía mensajes de WhatsApp a través de Twilio.
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")


def send_whatsapp(to_number: str, body: str) -> bool:
    """
    Envía un mensaje de WhatsApp vía Twilio.

    Args:
        to_number: Número destino, con o sin prefijo 'whatsapp:'
        body: Contenido del mensaje

    Returns:
        True si se envió exitosamente, False en caso de error
    """
    try:
        # Validar configuración
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM]):
            print("Error: Configuración de Twilio incompleta en .env")
            return False

        # Normalizar número destino (agregar prefijo si no lo tiene)
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        # Crear cliente Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Enviar mensaje
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            body=body,
            to=to_number
        )

        print(f"WhatsApp enviado a {to_number}: {message.sid}")
        return True

    except Exception as e:
        print(f"Error enviando WhatsApp a {to_number}: {e}")
        return False


if __name__ == "__main__":
    # Prueba del módulo
    import sys

    if len(sys.argv) < 3:
        print("Uso: python notify.py <numero_con_codigo_pais> <mensaje>")
        print("Ejemplo: python notify.py +1234567890 'Hola desde Cerca'")
        sys.exit(1)

    test_number = sys.argv[1]
    test_message = " ".join(sys.argv[2:])

    success = send_whatsapp(test_number, test_message)
    sys.exit(0 if success else 1)
