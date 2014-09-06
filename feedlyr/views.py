# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import View, TemplateView

from django import forms
# from django.forms.models import modelform_factory

from feedlyr.client import FeedlyClient
from feedlyr.models import SearchExpr, Source


FEEDLY_REDIRECT_URI = "http://localhost:8080"
FEEDLY_CLIENT_ID = "sandbox"
FEEDLY_CLIENT_SECRET = "YDRYI5E8OP2JKXYSDW79"


class ImportOPMLForm(forms.Form):
    opml_upload = forms.FileField('Upload de OPML', help_text='max 42 megabit')


class ImportOPMLView(View):
    form_class = ImportOPMLForm
    initial = {}
    template_name = 'feedlyr/opml.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            # Include message "Arquivo enviado com sucesso!"
            return render(request, self.template_name, {'form': form})


class SearchForm(forms.Form):
    """ Composição de formulários """

    # def __init__(self, *args, **kwargs):
    #     SourceForm = modelform_factory(Source,
    #                                    fields=('name', 'url'),
    #                                    exclude=('site',))
    #     SearchExprForm = modelform_factory(SearchExpr)
    #     self.source_form = SourceForm(prefix='source')
    #     self.expr_form = SearchExprForm(prefix='expr')


def get_feedly_client(token=None):
    if token:
        return FeedlyClient(token=token, sandbox=True)
    else:
        return FeedlyClient(client_id=FEEDLY_CLIENT_ID,
                            client_secret=FEEDLY_CLIENT_SECRET,
                            sandbox=True)


def feedly_new(request):
    """ Redirect the user to the feedly authorization URL to get user code
    """
    feedly = get_feedly_client()
    code_url = feedly.get_code_url(FEEDLY_REDIRECT_URI)
    return redirect(code_url)


def feedly_callback(request):
    """ After getting a code, exchange it for an access and a refresh token
    """

    # get/check params
    code = request.GET.get('code', '')
    if not code:
        return HttpResponse('The authentication is failed.')

    # get client and fetch access token
    feedly = get_feedly_client()
    res_access_token = feedly.get_access_token(FEEDLY_REDIRECT_URI, code)
    if 'errorCode' in res_access_token.keys():
        return HttpResponse('The authentication is failed.')
    access_token = res_access_token['access_token']

    # query the API
    user_subscriptions = feedly.get_user_subscriptions(access_token)
    return HttpResponse(user_subscriptions)


def feedly_logout(request):
    access_token = request.session.get('access_token', None)
    if access_token:
        feedly = get_feedly_client()
        feedly.feedly_logout(access_token=access_token,
                             client_id=FEEDLY_CLIENT_ID,
                             client_secret=FEEDLY_CLIENT_SECRET)
    return redirect('search')


class SearchView(TemplateView):
    """ Display checkboxes for registered sources and search expressions,
    with a searchbox which also enables adding new expressions.
    Also renders results.
    """

    form_class = SearchForm
    template_name = "feedlyr/base.html"

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['sources'] = Source.objects.all()
        context['exprs'] = SearchExpr.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        request.session['code'] = request.GET.get('code', '')
        return render(request, 'feedlyr/base.html', {'code': request.session['code']})

    def post(self, request, *args, **kwargs):
        """ Queries Feedly API for the search expression
        """
        feedly = get_feedly_client()
        query = request.POST.get('query', None)

        # Caso seja o primeiro acesso, autentica e solicita token de acesso
        access_token = request.session.get('access_token', None)
        query = request.POST.get('q', None)
        if not access_token:
            code = request.session['code']
            if not code:
                return redirect('feedly_new')
            res_access_token = feedly.get_access_token(FEEDLY_REDIRECT_URI, code)
            if 'errorCode' in res_access_token.keys():
                return HttpResponse('The authentication is failed.')
            access_token = request.session['access_token'] = res_access_token['access_token']

        results = feedly.search(access_token, query)
        results['query'] = query
        return render(request, 'feedlyr/base.html',
                      {'results': results, 'code': access_token})
