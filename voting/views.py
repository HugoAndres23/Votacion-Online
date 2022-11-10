from django.shortcuts import render, redirect, reverse
from account.views import account_login
from .models import Candidatura, Candidate, Voter, Votes
from django.http import JsonResponse
from django.utils.text import slugify
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
import requests
import json
# Create your views here.


def index(request):
    if not request.user.is_authenticated:
        return account_login(request)
    context = {}
    # return render(request, "voting/login.html", context)


def generate_ballot(display_controls=False):
    candidaturas = Candidatura.objects.order_by('priority').all()
    output = ""
    candidates_data = ""
    num = 1
    # return None
    for candidatura in candidaturas:
        nombre_candidatura = candidatura.nombre_candidatura
        Candidatura_nombre_candidatura = slugify(nombre_candidatura)
        candidates = Candidate.objects.filter(candidatura=candidatura)
        for candidate in candidates:
            if candidatura.maximo_votos > 1:
                instruction = "Puedes seleccionar " + \
                    str(candidatura.maximo_votos) + " candidatos"
                input_box = '<input type="checkbox" value="'+str(candidate.id)+'" class="flat-red ' + \
                    Candidatura_nombre_candidatura+'" name="' + \
                    Candidatura_nombre_candidatura+"[]" + '">'
            else:
                instruction = "Seleccione solo 1 candidato"
                input_box = '<input value="'+str(candidate.id)+'" type="radio" class="flat-red ' + \
                    Candidatura_nombre_candidatura+'" name="'+Candidatura_nombre_candidatura+'">'
            image = "/media/" + str(candidate.foto)
            candidates_data = candidates_data + '<li>' + input_box + '<button type="button" class="btn btn-primary btn-sm btn-flat clist platform" data-nombre_candidato="'+candidate.nombre_candidato+'" data-slogan="'+candidate.slogan+'"><i class="fa fa-search"></i> Información</button><img src="' + \
                image+'" height="100px" width="100px" class="clist"><span class="cname clist">' + \
                candidate.nombre_candidato+'</span></li>'
        up = ''
        if candidatura.priority == 1:
            up = 'disabled'
        down = ''
        if candidatura.priority == candidaturas.count():
            down = 'disabled'
        output = output + f"""<div class="row">	<div class="col-xs-12"><div class="box box-solid" id="{candidatura.id}">
             <div class="box-header with-border">
            <h3 class="box-title"><b>{nombre_candidatura}</b></h3>"""

        if display_controls:
            output = output + f""" <div class="pull-right box-tools">
        <button type="button" class="btn btn-default btn-sm moveup" data-id="{candidatura.id}" {up}><i class="fa fa-arrow-up"></i> </button>
        <button type="button" class="btn btn-default btn-sm movedown" data-id="{candidatura.id}" {down}><i class="fa fa-arrow-down"></i></button>
        </div>"""

        output = output + f"""</div>
        <div class="box-body">
        <p>{instruction}
        <span class="pull-right">
        <button type="button" class="btn btn-success btn-sm btn-flat reset" data-desc="{Candidatura_nombre_candidatura}"><i class="fa fa-refresh"></i> Reiniciar</button>
        </span>
        </p>
        <div id="candidate_list">
        <ul>
        {candidates_data}
        </ul>
        </div>
        </div>
        </div>
        </div>
        </div>
        """
        candidatura.priority = num
        candidatura.save()
        num = num + 1
        candidates_data = ''
    return output


def fetch_ballot(request):
    output = generate_ballot(display_controls=True)
    return JsonResponse(output, safe=False)


def generate_otp():
    """Link to this function
    https://www.codespeedy.com/otp-generation-using-random-module-in-python/
    """
    import random as r
    otp = ""
    for i in range(r.randint(5, 8)):
        otp += str(r.randint(1, 9))
    return otp


def dashboard(request):
    user = request.user
    # * Check if this voter has been verified
    if user.voter.otp is None or user.voter.verified == False:
        if not settings.SEND_OTP:
            # Bypass
            msg = bypass_otp()
            messages.success(request, msg)
            return redirect(reverse('show_ballot'))
        else:
            return redirect(reverse('voterVerify'))
    else:
        if user.voter.voted:  # * User has voted
            # To display election result or candidates I voted for ?
            context = {
                'my_votes': Votes.objects.filter(voter=user.voter),
            }
            return render(request, "voting/voter/result.html", context)
        else:
            return redirect(reverse('show_ballot'))


def verify(request):
    context = {
        'page_title': 'OTP Verification'
    }
    return render(request, "voting/voter/verify.html", context)


def resend_otp(request):
    """API For SMS
    I used https://www.multitexter.com/ API to send SMS
    You might not want to use this or this service might not be available in your Country
    For quick and easy access, Toggle the SEND_OTP from True to False in settings.py
    """
    user = request.user
    voter = user.voter
    error = False
    if settings.SEND_OTP:
        if voter.otp_sent >= 3:
            error = True
            response = "You have requested OTP three times. You cannot do this again! Please enter previously sent OTP"
        else:
            cédula = voter.cédula
            otp = voter.otp
            if otp is None:
                # Generate new OTP
                otp = generate_otp()
                voter.otp = otp
                voter.save()
            try:
                msg = "Dear " + str(user) + ", kindly use " + \
                    str(otp) + " as your OTP"
                message_is_sent = send_sms(cédula, msg)
                if message_is_sent:  # * OTP was sent successfully
                    # Update how many OTP has been sent to this voter
                    # Limited to Three so voters don't exhaust OTP balance
                    voter.otp_sent = voter.otp_sent + 1
                    voter.save()

                    response = "OTP has been sent to your cédula number. Please provide it in the box provided below"
                else:
                    error = True
                    response = "OTP not sent. Please try again"
            except Exception as e:
                response = "OTP could not be sent." + str(e)

                # * Send OTP
    else:
        #! Update all Voters record and set OTP to 0000
        #! Bypass OTP verification by updating verified to 1
        #! Redirect voters to ballot page
        response = bypass_otp()
    return JsonResponse({"data": response, "error": error})


def bypass_otp():
    Voter.objects.all().filter(otp=None, verified=False).update(otp="0000", verified=True)
    response = "Vote por el candidato que desee"
    return response


def send_sms(cédula_number, msg):
    """Read More
    https://www.multitexter.com/developers
    """
    import requests
    import os
    import json
    response = ""
    email = os.environ.get('SMS_EMAIL')
    password = os.environ.get('SMS_password')
    if email is None or password is None:
        raise Exception("Email/password no pueden estar vacios")
    url = "https://app.multitexter.com/v2/app/sms"
    data = {"email": email, "password": password, "message": msg,
            "sender_name": "OTP", "recipients": cédula_number, "forcednd": 1}
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(url, data=json.dumps(data), headers=headers)
    response = r.json()
    status = response.get('status', 0)
    if str(status) == '1':
        return True
    else:
        return False


def verify_otp(request):
    error = True
    if request.method != 'POST':
        messages.error(request, "Access Denied")
    else:
        otp = request.POST.get('otp')
        if otp is None:
            messages.error(request, "Please provide valid OTP")
        else:
            # Get User OTP
            voter = request.user.voter
            db_otp = voter.otp
            if db_otp != otp:
                messages.error(request, "Provided OTP is not valid")
            else:
                messages.success(
                    request, "You are now verified. Please cast your vote")
                voter.verified = True
                voter.save()
                error = False
    if error:
        return redirect(reverse('voterVerify'))
    return redirect(reverse('show_ballot'))


def show_ballot(request):
    if request.user.voter.voted:
        messages.error(request, "You have voted already")
        return redirect(reverse('voterDashboard'))
    ballot = generate_ballot(display_controls=False)
    context = {
        'ballot': ballot
    }
    return render(request, "voting/voter/ballot.html", context)


def preview_vote(request):
    if request.method != 'POST':
        error = True
        response = "Please browse the system properly"
    else:
        output = ""
        form = dict(request.POST)
        # We don't need to loop over CSRF token
        form.pop('csrfmiddlewaretoken', None)
        error = False
        data = []
        candidaturas = Candidatura.objects.all()
        for candidatura in candidaturas:
            maximo_votos = candidatura.maximo_votos
            pos = slugify(candidatura.nombre_candidatura)
            pos_id = candidatura.id
            if candidatura.maximo_votos > 1:
                this_key = pos + "[]"
                form_candidatura = form.get(this_key)
                if form_position is None:
                    continue
                if len(form_position) > maximo_votos:
                    error = True
                    response = "You can only choose " + \
                        str(maximo_votos) + " candidates for " + candidatura.nombre_candidatura
                else:
                    # for key, value in form.items():
                    start_tag = f"""
                       <div class='row votelist' style='padding-bottom: 2px'>
		                      	<span class='col-sm-4'><span class='pull-right'><b>{candidatura.nombre_candidatura} :</b></span></span>
		                      	<span class='col-sm-8'>
                                <ul style='list-style-type:none; margin-left:-40px'>
                                
                    
                    """
                    end_tag = "</ul></span></div><hr/>"
                    data = ""
                    for form_candidate_id in form_position:
                        try:
                            candidate = Candidate.objects.get(
                                id=form_candidate_id, candidatura=candidatura)
                            data += f"""
		                      	<li><i class="fa fa-check-square-o"></i> {candidate.nombre_candidato}</li>
                            """
                        except:
                            error = True
                            response = "Please, browse the system properly"
                    output += start_tag + data + end_tag
            else:
                this_key = pos
                form_position = form.get(this_key)
                if form_position is None:
                    continue
                # Max Vote == 1
                try:
                    form_position = form_position[0]
                    candidate = Candidate.objects.get(
                        candidatura=candidatura, id=form_position)
                    output += f"""
                            <div class='row votelist' style='padding-bottom: 2px'>
		                      	<span class='col-sm-4'><span class='pull-right'><b>{Candidatura.nombre_candidatura} :</b></span></span>
		                      	<span class='col-sm-8'><i class="fa fa-check-circle-o"></i> {candidate.nombre_candidato}</span>
		                    </div>
                      <hr/>
                    """
                except Exception as e:
                    error = True
                    response = "Please, browse the system properly"
    context = {
        'error': error,
        'list': output
    }
    return JsonResponse(context, safe=False)


def submit_ballot(request):
    if request.method != 'POST':
        messages.error(request, "Please, browse the system properly")
        return redirect(reverse('show_ballot'))

    # Verify if the voter has voted or not
    voter = request.user.voter
    if voter.voted:
        messages.error(request, "You have voted already")
        return redirect(reverse('voterDashboard'))

    form = dict(request.POST)
    form.pop('csrfmiddlewaretoken', None)  # Pop CSRF Token
    form.pop('submit_vote', None)  # Pop Submit Button

    # Ensure at least one vote is selected
    if len(form.keys()) < 1:
        messages.error(request, "Por favor seleccione un candidato")
        return redirect(reverse('show_ballot'))
    candidaturas = Candidatura.objects.all()
    form_count = 0
    for candidatura in candidaturas:
        maximo_votos = candidatura.maximo_votos
        pos = slugify(candidatura.nombre_candidatura)
        pos_id = candidatura.id
        if candidatura.maximo_votos > 1:
            this_key = pos + "[]"
            form_position = form.get(this_key)
            if form_position is None:
                continue
            if len(form_position) > maximo_votos:
                messages.error(request, "You can only choose " +
                               str(maximo_votos) + " candidates for " + candidatura.nombre_candidatura)
                return redirect(reverse('show_ballot'))
            else:
                for form_candidate_id in form_position:
                    form_count += 1
                    try:
                        candidate = Candidate.objects.get(
                            id=form_candidate_id, candidatura=candidatura)
                        vote = Votes()
                        vote.candidate = candidate
                        vote.voter = voter
                        vote.candidatura = candidatura
                        vote.save()
                    except Exception as e:
                        messages.error(
                            request, "Please, browse the system properly " + str(e))
                        return redirect(reverse('show_ballot'))
        else:
            this_key = pos
            form_position = form.get(this_key)
            if form_position is None:
                continue
            # Max Vote == 1
            form_count += 1
            try:
                form_position = form_position[0]
                candidate = Candidate.objects.get(
                    candidatura=candidatura, id=form_position)
                vote = Votes()
                vote.candidate = candidate
                vote.voter = voter
                vote.candidatura = candidatura
                vote.save()
            except Exception as e:
                messages.error(
                    request, "Please, browse the system properly " + str(e))
                return redirect(reverse('show_ballot'))
    # Count total number of records inserted
    # Check it viz-a-viz form_count
    inserted_votes = Votes.objects.filter(voter=voter)
    if (inserted_votes.count() != form_count):
        # Delete
        inserted_votes.delete()
        messages.error(request, "Intenta votar de nuevo.")
        return redirect(reverse('show_ballot'))
    else:
        # Update Voter profile to voted
        voter.voted = True
        voter.save()
        messages.success(request, "Gracias por votar")
        return redirect(reverse('voterDashboard'))
