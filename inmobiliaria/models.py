from django.db import models

# Create your models here.
class Propietario(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


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
        ('depto', 'Departamento'),
        ('local', 'Local'),
        ('otro', 'Otro')
    ]
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('arrendada', 'Arrendada'),
        ('vendida', 'Vendida')
    ]

    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name='propiedades')
    codigo = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=120)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='casa')
    dormitorios = models.IntegerField(default=0)
    baños = models.IntegerField(default=1)
    metros2 = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='disponible')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'

    def __str__(self):
        return f"{self.codigo} - {self.titulo} - {self.propietario.nombre}"