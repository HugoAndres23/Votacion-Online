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
    otp_sent = models.IntegerField(default=0)

    def __str__(self):
        return self.admin.apellido + ", " + self.admin.nombre


class Position(models.Model):
    name = models.CharField(max_length=50, unique=True)
    max_vote = models.IntegerField()
    priority = models.IntegerField()

    def __str__(self):
        return self.name


class Candidate(models.Model):
    fullname = models.CharField(max_length=50)
    photo = models.ImageField(upload_to="candidates")
    slogan = models.CharField(max_length=85, null=True)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)

    def __str__(self):
        return self.fullname


class Votes(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
