from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from sapl.utils import UF


def get_sessao_media_path(instance, subpath, filename):
    return './casa/%s/%s' % (subpath, filename)


def get_casa_media_path(instance, filename):
    return get_sessao_media_path(instance, 'Logotipo', filename)


class CasaLegislativa(models.Model):
    # TODO ajustar todos os max_length !!!!
    # cod_casa => id (pk)

    codigo = models.CharField(max_length=100, verbose_name=_('Codigo'))
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=100, verbose_name=_('Sigla'))
    endereco = models.CharField(max_length=100, verbose_name=_('Endereço'))
    cep = models.CharField(max_length=100, verbose_name=_('CEP'))
    municipio = models.CharField(max_length=100, verbose_name=_('Município'))
    uf = models.CharField(max_length=100,
                          choices=UF,
                          verbose_name=_('UF'))
    telefone = models.CharField(
        max_length=100, blank=True, verbose_name=_('Telefone'))
    fax = models.CharField(
        max_length=100, blank=True, verbose_name=_('Fax'))
    logotipo = models.ImageField(
        blank=True,
        upload_to=get_casa_media_path,
        verbose_name=_('Logotipo'))
    endereco_web = models.URLField(
        max_length=100, blank=True, verbose_name=_('HomePage'))
    email = models.EmailField(
        max_length=100, blank=True, verbose_name=_('E-mail'))
    informacao_geral = models.TextField(
        max_length=100,
        blank=True,
        verbose_name=_('Informação Geral'))

    class Meta:
        verbose_name = _('Casa Legislativa')
        verbose_name_plural = _('Casas Legislativas')


class ProblemaMigracao(models.Model):
    content_type = models.ForeignKey(ContentType,
                                     verbose_name=_('Tipo de Content'))
    object_id = models.PositiveIntegerField(verbose_name=_('ID do Objeto'))
    content_object = GenericForeignKey('content_type', 'object_id')
    problema = models.CharField(max_length=300, null=True,
                                verbose_name=_('Problema'))
    descricao = models.CharField(max_length=300, null=True,
                                 verbose_name=_('Descrição'))
    endereco = models.URLField(null=True, verbose_name=_('Endereço'))

    class Meta:
        verbose_name = _('Problema na Migração')
        verbose_name_plural = _('Problemas na Migração')
