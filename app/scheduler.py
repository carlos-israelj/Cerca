"""
Scheduler module: programa llamadas diarias automáticas para cada contacto.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from store import load_contacts
from caller import place_call


def schedule_calls():
    """
    Programa una llamada diaria para cada contacto activo,
    respetando su zona horaria y hora configurada.
    """
    scheduler = BlockingScheduler()

    # Cargar contactos
    contacts = load_contacts()

    if not contacts:
        print("Error: No se encontraron contactos para programar")
        return

    # Programar cada contacto activo
    scheduled_count = 0
    for contact in contacts:
        if not contact.get("active", False):
            print(f"Saltando contacto inactivo: {contact.get('id')}")
            continue

        contact_id = contact.get("id")
        call_time = contact.get("call_time", "09:00")
        timezone = contact.get("timezone", "America/Guayaquil")
        elder_name = contact.get("elder_name", "")

        # Parsear hora (formato HH:MM)
        try:
            hour, minute = call_time.split(":")
            hour = int(hour)
            minute = int(minute)
        except (ValueError, AttributeError):
            print(f"Error: Formato de call_time inválido para {contact_id}: {call_time}")
            continue

        # Crear trigger con la zona horaria del contacto
        try:
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=ZoneInfo(timezone)
            )

            # Agregar job al scheduler
            scheduler.add_job(
                func=place_call,
                trigger=trigger,
                args=[contact_id],
                id=f"call_{contact_id}",
                name=f"Llamada a {elder_name}",
                replace_existing=True
            )

            scheduled_count += 1
            print(f"✓ Programada llamada diaria a {elder_name} ({contact_id}) a las {call_time} {timezone}")

        except Exception as e:
            print(f"Error programando llamada para {contact_id}: {e}")
            continue

    if scheduled_count == 0:
        print("No se programó ninguna llamada. Verifica que haya contactos activos con configuración válida.")
        return

    # Mostrar resumen e iniciar scheduler
    print(f"\n{'='*60}")
    print(f"Scheduler iniciado con {scheduled_count} llamada(s) programada(s)")
    print(f"Presiona Ctrl+C para detener")
    print(f"{'='*60}\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler detenido")


if __name__ == "__main__":
    schedule_calls()
