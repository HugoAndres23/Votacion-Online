from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages


class AccountCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user  # Who is the current user ?
        if user.is_authenticated:
            if user.user_type == '1':  # Admin
                if modulename == 'voting.views':
                    error = True
                    if request.path == reverse('fetch_ballot'):
                        pass
                    else:
                        messages.error(
                            request, "No tienes permiso a esta recurso.")
                        return redirect(reverse('adminDashboard'))
            elif user.user_type == '2':  # Voter
                if modulename == 'administrador.views':
                    messages.error(
                        request, "No tienes acceso a este recurso.")
                    return redirect(reverse('voterDashboard'))
            else:  # Please take the user to login page
                return redirect(reverse('account_login'))
        else:
            # If the path is login or has anything to do with authentication, pass
            if request.path == reverse('account_login') or request.path == reverse('account_register') or modulename == 'django.contrib.auth.views' or request.path == reverse('account_login'):
                pass
            elif modulename == 'administrador.views' or modulename == 'voting.views':
                #
                messages.error(
                    request, "Necesitas estar logueado para realizar esta accion.")
                return redirect(reverse('account_login'))
            else:
                return redirect(reverse('account_login'))
