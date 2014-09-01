# -*- coding: utf-8 -*-
from django.db import models


class Group(models.Model):
    title = models.CharField('Nome do grupo', help_text='Nome do grupo de fontes de pesquisa', max_length=200)
    parent = models.ForeignKey('self')


class Source(models.Model):
    name = models.CharField('Nome do feed', help_text='Título da fonte', max_length=250)
    url = models.URLField('URL do feed', help_text='URL do feed')
    site = models.CharField('Site URL', help_text='URL do website associado a esta fonte', max_length=250)
    groups = models.ManyToManyField(Group, help_text='Grupos associados a esta fonte', null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Fonte de pesquisa'
        verbose_name_plural = 'Fontes de pesquisa'


class SearchExpr(models.Model):
    expr = models.CharField('Expressão de busca', max_length=250)

    def __unicode__(self):
        return self.expr
