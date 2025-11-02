import re
from django.core.exceptions import ValidationError
from PIL import Image

RUT_REGEX = re.compile(r"^(\d{1,2}\.?\d{3}\.?\d{3})-([\dkK])$")

def normalizar_rut(value: str) -> str:
    v = re.sub(r"[.\s]", "", value or "").upper()
    if "-" not in v and len(v) >= 2:
        v = f"{v[:-1]}-{v[-1]}"
    return v

def calcular_dv(rut_num: str) -> str:
    #rut_num sin DV, solo dígitos
    s = 0
    m = 2
    for d in rut_num[::-1]:
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - (s % 11)
    if r == 11:
        return "0"
    if r == 10:
        return "K"
    return str(r)

def validar_rut(value: str):
    v = normalizar_rut(value)
    m = RUT_REGEX.match(v)
    if not m:
        raise ValidationError("RUT inválido. Formato esperado: 12.345.678-5 o 12345678-5")
    rut_num = re.sub(r"\D", "", m.group(1))
    dv = m.group(2).upper()
    if calcular_dv(rut_num) != dv:
        raise ValidationError("Dígito verificador del RUT no coincide.")
    return v  #Devuelve normalizado opcionalmente

#Validación número celular
PHONE_REGEX = re.compile(r"^\+56\d{9}$")  # 9 dígitos luego de +56

def validar_telefono_cl(value):
    # Acepta None, "", tuple/list con 1 elem, y otros tipos.
    if value is None or value == "":
        return

    #Si es lista/tupla, usa el primer elemento
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return
        if len(value) > 1:
            raise ValidationError("Ingresa solo un número de teléfono.")
        value = value[0]

    #Asegura string
    if not isinstance(value, str):
        value = str(value)

    #Normaliza
    v = re.sub(r"[()\s-]", "", value)

    #Canociza a Chile
    if v.startswith("+56"):
        canon = v
    elif v.startswith("56"):
        canon = "+" + v
    elif len(v) == 9 and v[0] in "9":  # móvil típico chileno
        canon = f"+56{v}"
    else:
        raise ValidationError("Teléfono inválido. Usa formato +56912345678.")

    if not PHONE_REGEX.match(canon):
        raise ValidationError("Teléfono inválido. Formato requerido: +56912345678.")
    

def validar_imagen(imagen, max_mb=8, min_w=640, min_h=480):
    if imagen.size > max_mb * 1024 * 1024:
        raise ValidationError(f'La imagen supera {max_mb}MB.')
    img = Image.open(imagen)
    if img.width < min_w or img.height < min_h:
        raise ValidationError(f'Mínimo {min_w}x{min_h}px.')
    

def validar_pdf(archivo, max_mb=5):
    if not archivo:
        return
    if archivo.size > max_mb * 1024 * 1024:
        raise ValidationError(f"El archivo supera {max_mb} MB.")
    content_type = getattr(archivo, "content_type", "")
    if content_type not in ("application/pdf",):
        raise ValidationError("Solo se permiten archivos PDF.")