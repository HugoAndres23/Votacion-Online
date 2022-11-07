from django import forms
from .models import *
from account.forms import FormSettings


class VoterForm(FormSettings):
    class Meta:
        model = Voter
        fields = ['cédula']


class PositionForm(FormSettings):
    class Meta:
        model = Candidatura
        fields = ['nombre_candidatura', 'maximo_votos']


class CandidateForm(FormSettings):
    class Meta:
        model = Candidate
        fields = ['nombre_candidato', 'slogan', 'candidatura', 'foto']
