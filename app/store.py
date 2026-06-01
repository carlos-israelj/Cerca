"""
Store module: maneja la carga de contactos y memoria entre llamadas.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

# Rutas a los archivos de datos
BASE_DIR = Path(__file__).parent
CONTACTS_FILE = BASE_DIR / "contacts.json"
MEMORY_FILE = BASE_DIR / "memory.json"


def load_contacts() -> List[Dict[str, Any]]:
    """Carga la lista de contactos desde contacts.json."""
    try:
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("contacts", [])
    except FileNotFoundError:
        print(f"Error: {CONTACTS_FILE} no encontrado")
        return []
    except json.JSONDecodeError:
        print(f"Error: {CONTACTS_FILE} contiene JSON inválido")
        return []


def get_contact(contact_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un contacto específico por su ID."""
    contacts = load_contacts()
    for contact in contacts:
        if contact.get("id") == contact_id:
            return contact
    return None


def medications_text(contact: Dict[str, Any]) -> str:
    """
    Convierte la lista de medicamentos de hoy en una frase legible.
    Usa palabras en lugar de números para mejor pronunciación.
    """
    medications = contact.get("medications", [])
    if not medications:
        return "no tiene medicación programada para hoy"

    parts = []
    for med in medications:
        name = med.get("name", "medicamento")
        time = med.get("time", "")
        note = med.get("note", "")

        # Convertir hora numérica a palabras
        time_text = _format_time_as_words(time)

        med_text = f"{name}"
        if time_text:
            med_text += f" a {time_text}"
        if note:
            med_text += f" ({note})"

        parts.append(med_text)

    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} y {parts[1]}"
    else:
        return ", ".join(parts[:-1]) + f" y {parts[-1]}"


def _format_time_as_words(time_str: str) -> str:
    """
    Convierte hora en formato HH:MM a palabras.
    Ejemplo: "09:00" -> "las nueve de la mañana"
    """
    if not time_str or ":" not in time_str:
        return ""

    try:
        hour, minute = time_str.split(":")
        hour_num = int(hour)
        minute_num = int(minute)

        # Nombres de horas
        hour_names = {
            0: "doce", 1: "una", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco",
            6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 11: "once",
            12: "doce", 13: "una", 14: "dos", 15: "tres", 16: "cuatro", 17: "cinco",
            18: "seis", 19: "siete", 20: "ocho", 21: "nueve", 22: "diez", 23: "once"
        }

        hour_word = hour_names.get(hour_num, str(hour_num))

        # Determinar período del día
        if 5 <= hour_num < 12:
            period = "de la mañana"
        elif 12 <= hour_num < 20:
            period = "de la tarde"
        else:
            period = "de la noche"

        # Construir texto
        if minute_num == 0:
            return f"las {hour_word} {period}"
        else:
            # Convertir minutos a palabras también
            if minute_num == 30:
                return f"las {hour_word} y media {period}"
            elif minute_num == 15:
                return f"las {hour_word} y cuarto {period}"
            else:
                return f"las {hour_word} y {minute_num} minutos {period}"
    except (ValueError, IndexError):
        return time_str


def topics_text(contact: Dict[str, Any]) -> str:
    """Convierte la lista de temas en una cadena separada por comas."""
    topics = contact.get("topics", [])
    if not topics:
        return "temas de su interés"

    if len(topics) == 1:
        return topics[0]
    elif len(topics) == 2:
        return f"{topics[0]} y {topics[1]}"
    else:
        return ", ".join(topics[:-1]) + f" y {topics[-1]}"


def get_last_summary(contact_id: str) -> str:
    """
    Recupera el resumen de la última llamada desde memory.json.
    Retorna un texto por defecto si es la primera llamada o hay error.
    """
    try:
        if not MEMORY_FILE.exists():
            return "Esta es nuestra primera conversación."

        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)

        contact_memory = memory.get(contact_id, {})
        summary = contact_memory.get("last_summary", "")

        return summary if summary else "Esta es nuestra primera conversación."

    except (FileNotFoundError, json.JSONDecodeError):
        return "Esta es nuestra primera conversación."


def save_last_summary(contact_id: str, summary: str) -> None:
    """
    Guarda el resumen de la llamada en memory.json.
    Crea el archivo si no existe; es tolerante a errores.
    """
    try:
        # Cargar memoria existente o crear nueva
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    memory = json.load(f)
            except json.JSONDecodeError:
                memory = {}
        else:
            memory = {}

        # Actualizar memoria del contacto
        memory[contact_id] = {"last_summary": summary}

        # Guardar
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)

        print(f"Memoria guardada para {contact_id}")

    except Exception as e:
        print(f"Error guardando memoria para {contact_id}: {e}")
