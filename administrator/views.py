from django.shortcuts import render, reverse, redirect
from voting.models import Voter, Candidatura, Candidate, Votes
from account.models import CustomUser
from account.forms import CustomUserForm
from voting.forms import *
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import json  # Not used
from django_renderpdf.views import PDFView


def find_n_winners(data, n):
    """Read More
    https://www.geeksforgeeks.org/python-program-to-find-n-largest-elements-from-a-list/
    """
    final_list = []
    candidate_data = data[:]
    # print("Candidate = ", str(candidate_data))
    for i in range(0, n):
        max1 = 0
        if len(candidate_data) == 0:
            continue
        this_winner = max(candidate_data, key=lambda x: x['votes'])
        # TODO: Check if None
        this = this_winner['name'] + \
            " con " + str(this_winner['votes']) + " votes"
        final_list.append(this)
        candidate_data.remove(this_winner)
    return ", &nbsp;".join(final_list)


class PrintView(PDFView):
    template_name = 'admin/print.html'
    prompt_download = True

    @property
    def download_name(self):
        return "Resultados.pdf"

    def get_context_data(self, *args, **kwargs):
        title = "E-voting"
        try:
            file = open(settings.ELECTION_TITLE_PATH, 'r')
            title = file.read()
        except:
            pass
        context = super().get_context_data(*args, **kwargs)
        candidatura_data = {}
        for candidatura in candidatura.objects.all():
            candidate_data = []
            winner = ""
            for candidate in Candidate.objects.filter(candidatura=candidatura):
                this_candidate_data = {}
                votes = Votes.objects.filter(candidate=candidate).count()
                this_candidate_data['name'] = candidate.nombre_candidato
                this_candidate_data['votes'] = votes
                candidate_data.append(this_candidate_data)
            print("Candidate Data For  ", str(
                candidatura.name), " = ", str(candidate_data))
            # ! Check Winner
            if len(candidate_data) < 1:
                winner = "Esta candidatura no tiene candidatos"
            else:
                # Check if max_vote is more than 1
                if candidatura.max_vote > 1:
                    winner = find_n_winners(candidate_data, candidatura.max_vote)
                else:

                    winner = max(candidate_data, key=lambda x: x['votes'])
                    if winner['votes'] == 0:
                        winner = "Nadie a votado por esta candidatura"
                    else:
                        """
                        https://stackoverflow.com/questions/18940540/how-can-i-count-the-occurrences-of-an-item-in-a-list-of-dictionaries
                        """
                        count = sum(1 for d in candidate_data if d.get(
                            'votes') == winner['votes'])
                        if count > 1:
                            winner = f"There are {count} candidates with {winner['votes']} votes"
                        else:
                            winner = "Ganador : " + winner['name']
            print("Candidate Data For  ", str(
                candidatura.name), " = ", str(candidate_data))
            candidatura_data[candidatura.name] = {
                'candidate_data': candidate_data, 'winner': winner, 'max_vote': candidatura.max_vote}
        context['candidaturas'] = candidatura_data
        print(context)
        return context


def dashboard(request):
    candidaturas = Candidatura.objects.all().order_by('priority')
    candidates = Candidate.objects.all()
    voters = Voter.objects.all()
    voted_voters = Voter.objects.filter(voted=1)
    list_of_candidates = []
    votes_count = []
    chart_data = {}

    for candidatura in candidaturas:
        list_of_candidates = []
        votes_count = []
        for candidate in Candidate.objects.filter(candidatura=candidatura):
            list_of_candidates.append(candidate.nombre_candidato)
            votes = Votes.objects.filter(candidate=candidate).count()
            votes_count.append(votes)
        chart_data[candidatura] = {
            'candidates': list_of_candidates,
            'votes': votes_count,
            'pos_id': candidatura.id
        }

    context = {
        'candidatura_count': candidaturas.count(),
        'candidate_count': candidates.count(),
        'voters_count': voters.count(),
        'voted_voters_count': voted_voters.count(),
        'candidaturas': candidaturas,
        'chart_data': chart_data,
        'page_title': "Panel de control"
    }
    return render(request, "admin/home.html", context)


def voters(request):
    voters = Voter.objects.all()
    userForm = CustomUserForm(request.POST or None)
    voterForm = VoterForm(request.POST or None)
    context = {
        'form1': userForm,
        'form2': voterForm,
        'voters': voters,
        'page_title': 'Lista de votantes'
    }
    if request.method == 'POST':
        if userForm.is_valid() and voterForm.is_valid():
            voter = voterForm.save(commit=False)
            user = userForm.save(commit=False)
            voter.admin = user
            user.save()
            voter.save()
            messages.success(request, "Nuevo votante creado.")
        else:
            messages.error(request, "Votante no creado.")
    return render(request, "admin/voters.html", context)


def view_voter_by_id(request):
    voter_id = request.GET.get('id', None)
    voter = Voter.objects.filter(id=voter_id)
    context = {}
    if not voter.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        voter = voter[0]
        context['cédula'] = voter.cédula
        context['nombre'] = voter.admin.nombre
        context['apellido'] = voter.admin.apellido
        context['id'] = voter.id
        context['email'] = voter.admin.email
    return JsonResponse(context)


def view_candidatura_by_id(request):
    pos_id = request.GET.get('id', None)
    pos = candidatura.objects.filter(id=pos_id)
    context = {}
    if not pos.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        pos = pos[0]
        context['name'] = pos.name
        context['max_vote'] = pos.max_vote
        context['id'] = pos.id
    return JsonResponse(context)


def updateVoter(request):
    if request.method != 'POST':
        messages.error(request, "Access Denied")
    try:
        instance = Voter.objects.get(id=request.POST.get('id'))
        user = CustomUserForm(request.POST or None, instance=instance.admin)
        voter = VoterForm(request.POST or None, instance=instance)
        user.save()
        voter.save()
        messages.success(request, "Datos del votante")
    except:
        messages.error(request, "Acceso a este recurso denegado")

    return redirect(reverse('adminViewVoters'))


def deleteVoter(request):
    if request.method != 'POST':
        messages.error(request, "Acceso denegado")
    try:
        admin = Voter.objects.get(id=request.POST.get('id')).admin
        admin.delete()
        messages.success(request, "El votante a sido eliminado")
    except:
        messages.error(request, "Acceso denegado")

    return redirect(reverse('adminViewVoters'))


def viewcandidaturas(request):
    candidaturas = Candidatura.objects.order_by('-priority').all()
    form = PositionForm(request.POST or None)
    context = {
        'candidaturas': candidaturas,
        'form1': form,
        'page_title': "Candidaturas"
    }
    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.priority = candidaturas.count() + 1  # Just in case it is empty.
            form.save()
            messages.success(request, "Nueva candidatura creada.")
        else:
            messages.error(request, "Error de formato.")
    return render(request, "admin/positions.html", context)


def updatePosition(request):
    if request.method != 'POST':
        messages.error(request, "Acceso denegado")
    try:
        instance = candidatura.objects.get(id=request.POST.get('id'))
        pos = PositionForm(request.POST or None, instance=instance)
        pos.save()
        messages.success(request, "Candidatura modificada con exito!")
    except:
        messages.error(request, "Accesso denegado")

    return redirect(reverse('viewPositions'))


def deletePosition(request):
    if request.method != 'POST':
        messages.error(request, "Acceso denegado")
    try:
        pos = candidatura.objects.get(id=request.POST.get('id'))
        pos.delete()
        messages.success(request, "Candidatura eliminada.")
    except:
        messages.error(request, "Acceso denegado")

    return redirect(reverse('viewPositions'))


def viewCandidates(request):
    candidates = Candidate.objects.all()
    form = CandidateForm(request.POST or None, request.FILES or None)
    context = {
        'candidates': candidates,
        'form1': form,
        'page_title': 'Candidatos'
    }
    if request.method == 'POST':
        if form.is_valid():
            form = form.save()
            messages.success(request, "Nuevo candidato creado")
        else:
            messages.error(request, "Form errors")
    return render(request, "admin/candidates.html", context)


def updateCandidate(request):
    if request.method != 'POST':
        messages.error(request, "Acceso denegado")
    try:
        candidate_id = request.POST.get('id')
        candidate = Candidate.objects.get(id=candidate_id)
        form = CandidateForm(request.POST or None,
                             request.FILES or None, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Candidato actualizado.")
        else:
            messages.error(request, "Error en el formato.")
    except:
        messages.error(request, "Acceso denegado")

    return redirect(reverse('viewCandidates'))


def deleteCandidate(request):
    if request.method != 'POST':
        messages.error(request, "Acceso denegado")
    try:
        pos = Candidate.objects.get(id=request.POST.get('id'))
        pos.delete()
        messages.success(request, "Candidato eliminado.")
    except:
        messages.error(request, "Acceso denegado")

    return redirect(reverse('viewCandidates'))


def view_candidate_by_id(request):
    candidate_id = request.GET.get('id', None)
    candidate = Candidate.objects.filter(id=candidate_id)
    context = {}
    if not candidate.exists():
        context['code'] = 404
    else:
        candidate = candidate[0]
        context['code'] = 200
        context['nombre_candidato'] = candidate.nombre_candidato
        previous = CandidateForm(instance=candidate)
        context['form'] = str(previous.as_p())
    return JsonResponse(context)


def ballot_position(request):
    context = {
        'page_title': "Ballot Position"
    }
    return render(request, "admin/ballot_position.html", context)


def update_ballot_position(request, candidatura_id, up_or_down):
    try:
        context = {
            'error': False
        }
        candidatura = candidatura.objects.get(id=candidatura_id)
        if up_or_down == 'up':
            priority = candidatura.priority - 1
            if priority == 0:
                context['error'] = True
                output = "This candidatura is already at the top"
            else:
                candidatura.objects.filter(priority=priority).update(
                    priority=(priority+1))
                candidatura.priority = priority
                candidatura.save()
                output = "Moved Up"
        else:
            priority = candidatura.priority + 1
            if priority > candidatura.objects.all().count():
                output = "This candidatura is already at the bottom"
                context['error'] = True
            else:
                candidatura.objects.filter(priority=priority).update(
                    priority=(priority-1))
                candidatura.priority = priority
                candidatura.save()
                output = "Moved Down"
        context['message'] = output
    except Exception as e:
        context['message'] = e

    return JsonResponse(context)


def ballot_title(request):
    from urllib.parse import urlparse
    url = urlparse(request.META['HTTP_REFERER']).path
    from django.urls import resolve
    try:
        redirect_url = resolve(url)
        title = request.POST.get('title', 'No Name')
        file = open(settings.ELECTION_TITLE_PATH, 'w')
        file.write(title)
        file.close()
        messages.success(
            request, "La eleccion ha cambiado su titulo a " + str(title))
        return redirect(url)
    except Exception as e:
        messages.error(request, e)
        return redirect("/")


def viewVotes(request):
    votes = Votes.objects.all()
    context = {
        'votes': votes,
        'page_title': 'Votos'
    }
    return render(request, "admin/votes.html", context)


def resetVote(request):
    Votes.objects.all().delete()
    Voter.objects.all().update(voted=False, verified=False, otp=None)
    messages.success(request, "Todos los votos han sido reiniciados.")
    return redirect(reverse('viewVotes'))
