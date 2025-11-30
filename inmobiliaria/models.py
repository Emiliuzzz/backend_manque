from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import time
from .validators import * 
from .config import *
from django.contrib.auth.models import AbstractUser
from django.conf import settings



# Create your models here.

class Usuario(AbstractUser):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('PROPIETARIO', 'Propietario'),
        ('CLIENTE', 'Cliente'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='CLIENTE')
    aprobado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
    
class Propietario(models.Model):
    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100)
    primer_apellido = models.CharField(max_length=100)
    segundo_apellido = models.CharField(max_length=100)
    rut = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)


    def clean(self):
        #Normaliza y valida el Rut
        if self.rut:
            self.rut = normalizar_rut(self.rut)
            validar_rut(self.rut)
        #Valida teléfono
        if self.telefono:
            validar_telefono_cl(self.telefono)

    def save(self, *args, **kwargs):
        #Normaliza antes de guardar
        if self.rut:
            self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        partes = [
            self.primer_nombre, self.segundo_nombre,
            self.primer_apellido, self.segundo_apellido
        ]
        return " ".join(p for p in partes if p).strip()

    def __str__(self):
        return f"{self.nombre_completo} - {self.rut}"

class Region(models.Model):
    nombre_region = models.CharField(max_length=100)
    numero_region = models.IntegerField(default=7)

    class Meta:
        verbose_name = 'Region'
        verbose_name_plural = 'Regiones'

    def __str__(self):
        return self.nombre_region
    
    
class Comuna(models.Model):
    nombre_comuna = models.CharField(max_length=200)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="comunas")

    class Meta:
       unique_together = ('nombre_comuna', 'region')

    def __str__(self):
        return f"{self.nombre_comuna} ({self.region.nombre_region})"

class Direccion_propietario(models.Model):
    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name='direcciones')
    calle_o_pasaje = models.CharField(max_length=200)
    numero = models.CharField(max_length=40)
    poblacion_o_villa = models.CharField(max_length=200, blank=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.PROTECT, related_name='direcciones_propietario')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='direcciones_propietario')
    referencia = models.TextField(blank=True)
    codigo_postal = models.CharField(max_length=100, blank=True)
    principal = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = 'Dirección del propietario'
        verbose_name_plural = 'Direcciones del propietario'

    def __str__(self):
        return f"{self.calle_o_pasaje},{self.numero},{self.comuna.nombre_comuna}"

class Propiedad(models.Model):
    TIPO_CHOICES = [
        ('casa', 'Casa'),
        ('departamento', 'Departamento'),
        ('parcela', 'Parcela'),
        ('oficina', 'Oficina'),
        ('bodega', 'Bodega'),
        ('terreno', 'Terreno'),
    ]
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('arrendada', 'Arrendada'),
        ('reservada', 'Reservada'),
        ('vendida', 'Vendida'),
    ]

    ORIENTACION = [
        ('sur', 'Sur'),
        ('norte', 'Norte'),
        ('este', 'Este'),
        ('oeste', 'Oeste'),
    ]
    ESTADO_APROBACION = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('pausada', 'Pausada'),
    ]

    # campo existente
    aprobada = models.BooleanField(default=False)


    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name='propiedades')
    orientacion = models.CharField(max_length=30, choices=ORIENTACION, default='sur')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='casa')
    dormitorios = models.IntegerField(default=0,validators=[MinValueValidator(0)])
    baos = models.IntegerField(default=0,validators=[MinValueValidator(0)])
    metros2 = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                  validators=[MinValueValidator(0)])
    precio = models.DecimalField(max_digits=12, decimal_places=2,
                                 validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='disponible')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    propietario_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="propiedades_subidas",null=True, blank=True)
    estado_aprobacion = models.CharField(max_length=20, choices=ESTADO_APROBACION, default='pendiente')
    observacion_admin = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'
        indexes = [
            models.Index(fields=['estado', 'tipo']),
            models.Index(fields=['ciudad']),
            models.Index(fields=['precio']),      
            models.Index(fields=['aprobada']),    
        ]

    def save(self, *args, **kwargs):
        self.aprobada = (self.estado_aprobacion == "aprobada")
        from .models import Historial

        creando = self.pk is None
        old = None
        if not creando:
            try:
                old = Propiedad.objects.only('estado', 'precio').get(pk=self.pk)
            except Propiedad.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Registrar historial al crear
        if creando:
            try:
                Historial.objects.create(
                    propiedad=self,
                    accion='cambio_estado',
                    descripcion=f"Estado inicial: {self.estado}",
                )
                
                Historial.objects.create(
                    propiedad=self,
                    accion='actualizacion_precio',
                    descripcion=f"Precio inicial: {self.precio}",
                )
            except Exception:
                pass
            return

        # Registrar cambio de estado
        if old and old.estado != self.estado:
            try:
                Historial.objects.create(
                    propiedad=self,
                    accion='cambio_estado',
                    descripcion=f"Cambio de estado: {old.estado} → {self.estado}",
                )
            except Exception:
                pass

        # Registrar cambio de precio
        if old and old.precio != self.precio:
            try:
                Historial.objects.create(
                    propiedad=self,
                    accion='actualizacion_precio',
                    descripcion=f"Cambio de precio: {old.precio} → {self.precio}",
                )
            except Exception:
                pass
    
    @property
    def foto_principal(self):
        fp = self.fotos.filter(principal=True).first()
        return fp.foto.url if fp and fp.foto else None
    
    def __str__(self):
        return f"{self.orientacion} - {self.titulo} - {self.propietario.primer_nombre}"



# Tabla interesados:
class Interesado(models.Model):
    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100)
    primer_apellido = models.CharField(max_length=100)
    segundo_apellido = models.CharField(max_length=100)
    rut = models.CharField(max_length=20, unique=True, validators=[validar_rut]) 
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,related_name="perfil_interesado")

    def clean(self):
        from .validators import normalizar_rut, validar_rut, validar_telefono_cl
        if self.rut:
            self.rut = normalizar_rut(self.rut)
            validar_rut(self.rut)
        if self.telefono:
            validar_telefono_cl(self.telefono)

    # Junta nombres y apellidos
    @property
    def nombre_completo(self):
        partes = [
            self.primer_nombre, self.segundo_nombre,
            self.primer_apellido, self.segundo_apellido
        ]
        return " ".join(p for p in partes if p).strip()

    def __str__(self):
        return f"{self.nombre_completo} - {self.rut}"
    


class SolicitudCliente(models.Model):
    TIPO_OPERACION = [
        ("COMPRA", "Compra"),
        ("ARRIENDO", "Arriendo"),
    ]

    ESTADO_SOLICITUD = [
        ("nueva", "Nueva"),
        ("en_proceso", "En proceso"),
        ("respondida", "Respondida"),
        ("cerrada", "Cerrada"),
    ]

    interesado = models.ForeignKey(
        Interesado,
        on_delete=models.CASCADE,
        related_name="solicitudes"
    )

    tipo_operacion = models.CharField(max_length=20, choices=TIPO_OPERACION)
    tipo_propiedad = models.CharField(
        max_length=20,
        choices=Propiedad.TIPO_CHOICES,
        default="casa",
    )

    ciudad = models.CharField(max_length=120)
    comuna = models.CharField(max_length=120)

    presupuesto_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    presupuesto_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    mensaje = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_SOLICITUD,
        default="nueva",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["estado", "created_at"]),
        ]

    def __str__(self):
        return f"Solicitud de {self.interesado.nombre_completo} ({self.tipo_operacion} {self.tipo_propiedad})"
    
    
# Tabla Visitas:
MAX_VISITAS_POR_DIA = 2 
class Visita(models.Model):
    propiedad   = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='visitas')
    interesado  = models.ForeignKey(Interesado, on_delete=models.CASCADE, related_name='visitas')
    fecha       = models.DateField()
    hora       = models.TimeField()
    estado      = models.CharField(max_length=100, default='agendada')  # agendada, confirmada, realizada, cancelada
    comentarios = models.TextField(blank=True)

    class Meta:
        unique_together = ('propiedad', 'interesado', 'fecha', 'hora')
        indexes = [models.Index(fields=['fecha', 'hora', 'estado'])]

    def clean(self):
        from .utils import slots_futuro
        hoy = timezone.localdate()

        # ventana futura
        delta = (self.fecha - hoy).days
        if delta < 0 or delta > VENTANA_FUTURA_MAX_DIAS:
            raise ValidationError(f"La fecha debe estar entre hoy y {VENTANA_FUTURA_MAX_DIAS} días en el futuro.")

        # lunes a viernes
        if self.fecha.weekday() > 4:
            raise ValidationError("Las visitas solo se pueden agendar de lunes a viernes.")

        # slots válidos
        if self.hora not in INTERVALO_PERMITIDOS:
            raise ValidationError("La hora debe ser un slot válido: 09–13 o 16–18 (en punto).")

        # no permite pasado
        if not slots_futuro(self.fecha, self.hora):
            raise ValidationError("La hora seleccionada ya pasó o está fuera del margen mínimo.")

        # doble booking propiedad/slot
        qs = Visita.objects.filter(propiedad=self.propiedad, fecha=self.fecha, hora=self.hora)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError("Ese horario ya está reservado para la propiedad.")
        
        visitas_dia = Visita.objects.filter(
            interesado=self.interesado,
            fecha=self.fecha,
            estado__in=["agendada", "confirmada"]  # considera solo activas
        )
        if self.pk:
            visitas_dia = visitas_dia.exclude(pk=self.pk)
        if visitas_dia.count() >= MAX_VISITAS_POR_DIA:
            raise ValidationError(f"El interesado ya alcanzó el máximo de {MAX_VISITAS_POR_DIA} visitas para ese día.")

# Tabla dias feriados
class Feriado(models.Model):
    fecha = models.DateField(unique=True)
    nombre = models.CharField(max_length=120)

    class Meta:
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.fecha} - {self.nombre}"


# Tabla Reservas
class Reserva(models.Model):
    propiedad = models.ForeignKey("Propiedad", on_delete=models.CASCADE, related_name="reservas", db_index=True)
    interesado = models.ForeignKey("Interesado", on_delete=models.CASCADE, related_name="reservas", db_index=True)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    monto_reserva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notas = models.TextField(blank=True)
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["propiedad", "activa"]),
            models.Index(fields=["expires_at"]),
        ]

    def clean(self):
        # Solo una reserva activa por propiedad
        if self.activa:
            existe_otra = Reserva.objects.filter(propiedad=self.propiedad, activa=True).exclude(pk=self.pk).exists()
            if existe_otra:
                raise ValidationError("La propiedad ya tiene una reserva activa.")

        # No permitir reserva si hay contrato vigente
        from .models import Contrato
        if Contrato.objects.filter(propiedad=self.propiedad, vigente=True).exists():
            raise ValidationError("La propiedad ya posee un contrato vigente.")


        # Debe tener fecha de vencimiento si está activa
        if self.activa and not self.expires_at:
            raise ValidationError("Debe definir 'expires_at' para la reserva activa.")

        # expires_at > ahora
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError("La fecha de vencimiento debe ser futura.")

    def save(self, *args, **kwargs):
        self.clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.activa:
                # Cambia el estado de la propiedad a RESERVADA
                self.propiedad.estado = "reservada"
                self.propiedad.save(update_fields=["estado"])
    def __str__(self):
        return f"{self.propiedad} - {self.interesado}"

class Contrato(models.Model):
    TIPO = (("venta","Venta"),("arriendo","Arriendo"))
    propiedad = models.ForeignKey(Propiedad, on_delete=models.PROTECT, related_name="contratos")
    comprador_arrendatario = models.ForeignKey(Interesado, on_delete=models.PROTECT, related_name="contratos")
    tipo = models.CharField(max_length=10, choices=TIPO)
    fecha_firma = models.DateField()
    precio_pactado = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    vigente = models.BooleanField(default=True)
    archivo_pdf = models.FileField(upload_to="contratos/", blank=True, null=True, validators=[validar_pdf])

    archivo_pdf = models.FileField(
        upload_to='contratos/',
        blank=True,
        null=True,
        verbose_name='Archivo PDF del contrato'
    )
    class Meta:
        indexes = [models.Index(fields=["tipo","vigente"])]

    def __str__(self):
        return f"{self.tipo.title()} {self.propiedad.titulo} - {self.comprador_arrendatario.nombre_completo}"
    

# Tabla Pago
class Pago(models.Model):

    MEDIOS_PAGO = [
        ("transferencia", "Transferencia"),
        ("efectivo", "Efectivo"),
        ("tarjeta_debito", "Tarjeta de débito"),
        ("tarjeta_credito", "Tarjeta de crédito"),
        ("cheque", "Cheque"),
        ("webpay", "Webpay"),
        ("otro", "Otro"),
    ]
    
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name="pagos")
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    medio = models.CharField(max_length=30, choices=MEDIOS_PAGO, default="transferencia")
    comprobante = models.FileField(upload_to="pagos/", blank=True, null=True)
    notas = models.TextField(blank=True)

    comprobante = models.FileField(
        upload_to='pagos/',
        blank=True,
        null=True,
        verbose_name='Comprobante / boleta'
    )    
    
    def __str__(self):
        return f"Pago {self.monto} - {self.contrato}"
    


from django.db import transaction


class PropiedadFoto(models.Model):
    propiedad = models.ForeignKey('Propiedad', on_delete=models.CASCADE, related_name='fotos')
    foto = models.ImageField(upload_to='propiedades/fotos/', validators=[validar_imagen])
    orden = models.PositiveIntegerField(default=0, db_index=True)
    principal = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['propiedad', 'orden']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.principal:
                (PropiedadFoto.objects
                 .filter(propiedad=self.propiedad)
                 .exclude(pk=self.pk)
                 .update(principal=False))



# Tabla documentos propiedad
class PropiedadDocumento(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name="documentos")
    nombre = models.CharField(max_length=150)
    archivo = models.FileField(upload_to="propiedades/docs/")
    subido = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.propiedad.orientacion} - {self.nombre}"
    


#Tabla historial de cambios
class Historial(models.Model):

    ACCION = [
        ('cambio_estado', 'Cambio de estado'),
        ('actualizacion_precio', 'Actualización de precio'),
    ]

    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name="historial")
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=100, choices= ACCION, default= 'cambio_estado')
    descripcion = models.TextField(blank=True)
    usuario = models.CharField(max_length=100, blank=True) 

    class Meta:
        ordering = ['-fecha']
        indexes = [models.Index(fields=["accion", "fecha"])]
        verbose_name = "Historial"
        verbose_name_plural = "Historial"

    def __str__(self):
        return f"{self.propiedad.titulo} - {self.accion} ({self.fecha.date()})"
    


#Tabla comisión

class Comision(models.Model):
    contrato = models.OneToOneField('Contrato', on_delete=models.CASCADE, related_name="comision")
    porcentaje_comprador = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    porcentaje_vendedor  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fija_comprador = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fija_vendedor  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notas = models.TextField(blank=True)

    def total_estimada(self, base=None):
        if base is None:
            base = self.contrato.precio_pactado
        return (
            base * ((self.porcentaje_comprador + self.porcentaje_vendedor) / 100)
            + self.fija_comprador + self.fija_vendedor
        )
    
    def __str__(self):
        return f"Comisión de {self.contrato}"
    


#Tabla cuota contrato
class CuotaContrato(models.Model):
    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE, related_name="cuotas")
    vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    pagada = models.BooleanField(default=False)
    pago = models.ForeignKey("Pago", null=True, blank=True, on_delete=models.SET_NULL, related_name="cuotas_asociadas")

    class Meta:
        ordering = ["vencimiento"]
        indexes = [models.Index(fields=["vencimiento", "pagada"])]

    from django.db import transaction

    def registrar_pago(self, *, monto, fecha=None, medio="transferencia", comprobante=None, notas=""):
        # Marca esta cuota como pagada
        if self.pagada:
            raise ValidationError("Esta cuota ya está pagada.")
        if monto != self.monto:
            raise ValidationError("El monto del pago debe coincidir con el monto de la cuota.")

        from .models import Pago 
        if fecha is None:
            fecha = timezone.localdate()

        with transaction.atomic():
            pago = Pago.objects.create(
                contrato=self.contrato,
                fecha=fecha,
                monto=monto,
                medio=medio,
                comprobante=comprobante,
                notas=notas,
            )
            self.pagada = True
            self.pago = pago
            self.save(update_fields=["pagada", "pago"])
            return pago

    def __str__(self):
        estado = "Pagada" if self.pagada else "Pendiente"
        return f"Cuota {self.contrato} - {self.vencimiento} ({estado})"
    
# Tabla notificaciones
class Notificacion(models.Model):
    TIPOS = [
        ("RESERVA", "Reserva"),
        ("VISITA", "Visita"),
        ("PAGO", "Pago"),
        ("SISTEMA", "Sistema"),
    ]
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="notificaciones")
    titulo = models.CharField(max_length=120)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=16, choices=TIPOS, default="SISTEMA", db_index=True)
    leida = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tipo", "leida", "created_at"])]
        verbose_name = "Notificacion"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"[{self.tipo}] {self.titulo}"
