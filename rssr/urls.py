from django.conf.urls import patterns, include, url
from feedlyr import views
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.SearchView.as_view(), name='search'),
    url(r'^feedly_new', views.feedly_new, name='feedly_new'),
    url(r'^feedly_callback', views.feedly_callback, name='feedly_callback'),
    url(r'^feedly_logout', views.feedly_logout, name='feedly_logout'),
    url(r'^import/$', views.ImportOPMLView.as_view(), name='import'),
    # url(r'^export-(?P<now>\d{8}-\d{4})$', views.ExportView.as_view(), name='export'),
    url(r'^export$', views.ExportView.as_view(), name='export'),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns = format_suffix_patterns(urlpatterns)
