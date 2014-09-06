from django.conf.urls import patterns, include, url
from feedlyr import views
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.SearchView.as_view(), name='search'),
    url(r'^feedly_new', views.feedly_new, name='feedly_new'),
    url(r'^feedly_callback', views.feedly_callback, name='feedly_callback'),
    url(r'^feedly_logout', views.feedly_logout, name='feedly_logout'),
    url(r'^opml/', views.ImportOPMLView.as_view(), name='opml'),
    url(r'^admin/', include(admin.site.urls)),
)
