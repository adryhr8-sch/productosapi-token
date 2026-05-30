from django.db import models

# Create your models here.

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    descripción = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    categoría = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
