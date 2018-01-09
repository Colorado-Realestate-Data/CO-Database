from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from project.helpers.utils import PermissionRequiredMixin


@method_decorator(csrf_exempt, name='dispatch')
class IndexView(PermissionRequiredMixin, View):
    permission_required = ()

    def get(self, request, *args, **kwargs):
        return redirect('/static/index.html')

    def post(self, request, *args, **kwargs):
        return redirect('/static/index.html')


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            next_url = request.GET.get('next') or settings.LOGIN_REDIRECT_URL
            return redirect(next_url)
        return render(request, self.template_name)
