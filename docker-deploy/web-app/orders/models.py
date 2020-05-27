from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.postgres.fields import ArrayField

class Order(models.Model):
    STATUS_CHOICES = (
        ('status1', 'Truck en route to warehouse'),
        ('status2', 'truck waiting for package'),
        ('status3', 'out for delivery'),
        ('status4', 'delivered'),
    )

    #accounts info 
    uAccount = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    worldid = models.IntegerField(default=0)

    #order info
    package_id = models.IntegerField(default=0)
    truck_id = models.IntegerField(default=0)
    destination_x = models.IntegerField(default=0)
    destination_y = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='status1')
    products_num = ArrayField(models.IntegerField(default=0), size=100, blank=True, null=True)
    products_id = ArrayField(models.IntegerField(default=0), size=100, blank=True, null=True)
    products_description = ArrayField(models.CharField(max_length=50), size=100, blank=True, null=True)
    
    
    def __str__(self):
        return str(self.status)

    def get_absolute_url(self):
        return reverse('order-detail', kwargs = {'pk': self.pk})


