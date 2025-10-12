from datetime import time, timedelta

#Intervalos permitidos
INTERVALO_MANANA = (time(9), time(10), time(11), time(12), time(13))
INTERVALO_TARDE  = (time(16), time(17), time(18))
INTERVALO_PERMITIDOS = INTERVALO_MANANA + INTERVALO_TARDE

#Ventana futura seleccionable
VENTANA_FUTURA_MAX_DIAS = 30


MAX_VISITAS_ACTIVAS_POR_INTERESADO = 3

#Estado de la visita
ESTADOS_ACTIVOS = ("agendada", "confirmada")

#Tamaño por defecto de "scroll"
DEFAULT_DAYS_PAGE = 14
MAX_DAYS_PAGE = 31


# Minutos minimos antes de la reservación
LEAD_MINUTES = 0