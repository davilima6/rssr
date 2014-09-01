from django.conf.urls import patterns, include, url
from feedlyr import views
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.SearchView.as_view(), name='search'),
    url(r'^feedly_new', views.feedly_new, name='feedly_new'),
    url(r'^feedly_callback', views.feedly_callback, name='feedly_callback'),
    url(r'^admin/', include(admin.site.urls)),
)
