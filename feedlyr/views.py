# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import View, TemplateView

from django import forms
# from django.forms.models import modelform_factory

from feedlyr.client import FeedlyClient
from feedlyr.models import SearchExpr, Source

from rest_framework.renderers import JSONRenderer
from rest_framework.renderers import XMLRenderer
# from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_csv.renderers import CSVRenderer
# from rest_pandas.renderers import PandasExcelRenderer
# from rest_pandas.renderers import PandasCSVRenderer

# DEV CLOUD
# FEEDLY_REDIRECT_URI = "http://104.131.52.43"
# FEEDLY_CLIENT_ID = "c85cb160-45e0-4a80-aefd-03e7e3bf464f"
# FEEDLY_CLIENT_SECRET = "AkrjI4B7ImEiOiJGZWVkbHkgRGV2ZWxvcGVyIiwiZSI6MTQxODU5NTYwNjc2NCwiaSI6ImM4NWNiMTYwLTQ1ZTAtNGE4MC1hZWZkLTAzZTdlM2JmNDY0ZiIsInAiOjYsInQiOjEsInYiOiJwcm9kdWN0aW9uIiwidyI6IjIwMTMuNDMiLCJ4Ijoic3RhbmRhcmQifQ:feedlydev"

# DEV SANDBOX
# FEEDLY_REDIRECT_URI = "http://104.131.52.43"
# FEEDLY_CLIENT_ID = "sandbox"
# FEEDLY_CLIENT_SECRET = "A0SXFX54S3K0OC9GNCXG"

# LOCAL SANDBOX
FEEDLY_REDIRECT_URI = "http://localhost:8080"
FEEDLY_CLIENT_ID = "sandbox"
FEEDLY_CLIENT_SECRET = "A0SXFX54S3K0OC9GNCXG"


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

        # Caso seja o primeiro acesso, autentica e solicita token de acesso
        access_token = request.session.get('access_token', None)
        if not access_token:
            code = request.session['code']
            if not code:
                return redirect('feedly_new')
            res_access_token = feedly.get_access_token(FEEDLY_REDIRECT_URI, code)
            if 'errorCode' in res_access_token.keys():
                return HttpResponse('The authentication is failed.')
            access_token = request.session['access_token'] = res_access_token['access_token']

        query = request.POST.get('q', None)
        results = feedly.search(access_token, query)
        if results.get('errorCode'):
            return render(request, 'feedlyr/base.html',
                          {'error': '{}'.format(results)})
        request.session['results'] = results
        sources = {item['origin']['title'] for item in results['items']}
        categories = {category[0]['label'] for category in [item['categories'] for item in results['items']]}
        return render(request, 'feedlyr/base.html',
                      {'code': access_token,
                       'query': query,
                       'results': results,
                       'sources': sources,
                       'categories': categories,
                       })


class ImportOPMLForm(forms.Form):
    opml_upload = forms.FileField(label='Arquivo OPML')


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


class ExportView(APIView):
    """ TODO: TemplateHTMLRenderer, PandasExcelRenderer, PandasCSVRenderer
    """
    renderer_classes = (JSONRenderer, XMLRenderer, CSVRenderer, )

    def get(self, request, format=None):
        """
        Serializa resultados persistidos na sessão para formato solicitado:
        JSON, CSV, XML, HTML etc.
        """

        data = request.session['results']['items']

        if request.accepted_renderer.format == 'html':
            return Response(data, template_name='feedlyr/results.html')

        return Response(data)
