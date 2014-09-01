from django.contrib import admin
from feedlyr.models import Source, SearchExpr


class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')
    list_filter = ['groups', 'name']
    search_fields = ['name', 'url']

    fieldsets = (
        (None, {'fields': ('name', 'url', 'site')}),
        ('Groups', {'fields': ('groups',)})
    )

    verbose_name = 'Fonte'


admin.site.register(Source, SourceAdmin)
admin.site.register(SearchExpr)
