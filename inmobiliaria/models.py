from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import time
from .validators import * 
from .config import *


# Create your models here.
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
        ('este', 'Este'),
    ]
    #Hacer el select de sur, norte, este u oeste de la ciudad

    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name='propiedades')
    orientación = models.CharField(max_length=30,choices= ORIENTACION, default= 'sur')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='casa')
    dormitorios = models.PositiveIntegerField(default=0)
    baños = models.PositiveIntegerField(default=1)
    metros2 = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                  validators=[MinValueValidator(0)])
    precio = models.DecimalField(max_digits=12, decimal_places=2,
                                 validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='disponible')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'
        indexes = [
            models.Index(fields=["estado", "tipo"]),
            models.Index(fields=["ciudad"]),
        ]


    def __str__(self):
        return f"{self.orientación} - {self.titulo} - {self.propietario.primer_nombre}"
    



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
    



# Tabla Visitas:
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
    propiedad = models.ForeignKey(Propiedad, on_delete=models.PROTECT, related_name="reservas")
    interesado = models.ForeignKey(Interesado, on_delete=models.PROTECT, related_name="reservas")
    fecha = models.DateTimeField(auto_now_add=True)
    monto_reserva = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    activa = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["activa"])]

    def __str__(self):
        return f"Reserva {self.propiedad.orientación} - {self.interesado.nombre_completo}"
    
# Tabla Contratos
class Contrato(models.Model):
    TIPO = (("venta","Venta"),("arriendo","Arriendo"))
    propiedad = models.ForeignKey(Propiedad, on_delete=models.PROTECT, related_name="contratos")
    comprador_arrendatario = models.ForeignKey(Interesado, on_delete=models.PROTECT, related_name="contratos")
    tipo = models.CharField(max_length=10, choices=TIPO)
    fecha_firma = models.DateField()
    precio_pactado = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    vigente = models.BooleanField(default=True)
    archivo_pdf = models.FileField(upload_to="contratos/", blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["tipo","vigente"])]

    def __str__(self):
        return f"{self.tipo.title()} {self.propiedad.orientación} - {self.comprador_arrendatario.nombre_completo}"
    

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

    def __str__(self):
        return f"Pago {self.monto} - {self.contrato}"
    

#Tabla foto principal de la propiedad
class PropiedadFoto(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name="fotos")
    foto = models.ImageField(upload_to="propiedades/fotos/")
    orden = models.PositiveIntegerField(default=0)
    principal = models.BooleanField(default=False)

    class Meta:
        ordering = ["propiedad","orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["propiedad"],
                condition=models.Q(principal=True),
                name="una_foto_por_propiedad",
            )
        ]


# Tabla documentos propiedad
class PropiedadDocumento(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name="documentos")
    nombre = models.CharField(max_length=150)
    archivo = models.FileField(upload_to="propiedades/docs/")
    subido = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.propiedad.codigo} - {self.nombre}"