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
        fields = ['name', 'max_vote']


class CandidateForm(FormSettings):
    class Meta:
        model = Candidate
        fields = ['fullname', 'slogan', 'candidatura', 'foto']
