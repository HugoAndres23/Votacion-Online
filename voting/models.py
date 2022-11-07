from unittest.util import _MAX_LENGTH
from django.db import models
from account.models import CustomUser
# Create your models here.


class Voter(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    cédula = models.PositiveIntegerField(min_value=10000000, max_value=9999999999, unique=True)
    otp = models.CharField(max_length=10, null=True)
    verified = models.BooleanField(default=False)
    voted = models.BooleanField(default=False)
    otp_sent = models.IntegerField(default=0)  # Control how many OTPs are sent

    def __str__(self):
        return self.admin.apellido + ", " + self.admin.nombre


class Candidatura(models.Model):
    nombre_candidatura = models.CharField(max_length=50, unique=True)
    maximo_votos = models.IntegerField()
    priority = models.IntegerField()

    def __str__(self):
        return self.nombre_candidatura


class Candidate(models.Model):
    nombre_candidato = models.CharField(max_length=50)
    foto = models.ImageField(upload_to="candidates")
    slogan = models.CharField(max_length=85, null=True)
    candidatura = models.ForeignKey(Candidatura, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_candidato


class Votes(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidatura = models.ForeignKey(Candidatura, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
