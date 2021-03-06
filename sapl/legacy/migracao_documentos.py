import mimetypes
import os
import re

import magic

from django.db.models.signals import post_delete, post_save
from sapl.base.models import CasaLegislativa
from sapl.materia.models import (DocumentoAcessorio, MateriaLegislativa,
                                 Proposicao)
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MEDIA_ROOT
from sapl.utils import delete_texto, save_texto


# MIGRAÇÃO DE DOCUMENTOS  ###################################################
EXTENSOES = {
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',  # noqa
    'application/xml': '.xml',
    'application/zip': '.zip',
    'image/jpeg': '.jpeg',
    'image/png': '.png',
    'text/html': '.html',
    'text/rtf': '.rtf',
    'text/x-python': '.py',

    # sem extensao
    'application/octet-stream': '',  # binário
    'inode/x-empty': '',  # vazio
}

DOCS = {
    CasaLegislativa: [(
        'logotipo',
        'props_sapl/logo_casa.gif',
        'casa/logotipo/logo_casa.gif')],
    Parlamentar: [(
        'fotografia',
        'parlamentar/fotos/{}_foto_parlamentar',
        'parlamentar/{0}/{0}_foto_parlamentar{1}')],
    MateriaLegislativa: [(
        'texto_original',
        'materia/{}_texto_integral',
        'materialegislativa/{0}/{0}_texto_integral{1}')],
    DocumentoAcessorio: [(
        'arquivo',
        'materia/{}',
        'documentoacessorio/{0}/{0}{1}')],
    NormaJuridica: [(
        'texto_original',
        'norma_juridica/{}_texto_integral',
        'normajuridica/{0}/{0}_texto_integral{1}')],
    SessaoPlenaria: [
        ('upload_ata',
         'ata_sessao/{}_ata_sessao',
         'sessaoplenaria/{0}/ata/{0}_ata_sessao{1}'),
        ('upload_anexo',
         'anexo_sessao/{}_texto_anexado',
         'sessaoplenaria/{0}/anexo/{0}_texto_anexado{1}')
    ],
    Proposicao: [(
        'texto_original',
        'proposicao/{}',
        'proposicao/{0}/{0}{1}')],
    DocumentoAdministrativo: [(
        'texto_integral',
        'administrativo/{}_texto_integral',
        'documentoadministrativo/{0}/{0}_texto_integral{1}')],
}

DOCS = {tipo: [(campo,
                os.path.join('sapl_documentos', origem),
                os.path.join('sapl', destino))
               for campo, origem, destino in campos]
        for tipo, campos in DOCS.items()}


def em_media(caminho):
    return os.path.join(MEDIA_ROOT, caminho)


def mover_documento(origem, destino):
    origem, destino = [em_media(c) if not os.path.isabs(c) else c
                       for c in (origem, destino)]
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    os.rename(origem, destino)


def get_casa_legislativa():
    casa = CasaLegislativa.objects.first()
    if not casa:
        casa = CasaLegislativa.objects.create(**{k: 'PREENCHER...' for k in [
            'codigo', 'nome', 'sigla', 'endereco', 'cep', 'municipio', 'uf',
        ]})
    return casa


def migrar_docs_logo():
    print('#### Migrando logotipo da casa ####')
    [(_, origem, destino)] = DOCS[CasaLegislativa]
    props_sapl = os.path.dirname(origem)
    # a pasta props_sapl deve conter apenas o origem e metadatas!
    assert set(os.listdir(em_media(props_sapl))) < {
        'logo_casa.gif', '.metadata', 'logo_casa.gif.metadata'}
    mover_documento(origem, destino)
    casa = get_casa_legislativa()
    casa.logotipo = destino
    casa.save()


def get_extensao(caminho):
    mime = magic.from_file(caminho, mime=True)
    try:
        return EXTENSOES[mime]
    except KeyError as e:
        raise Exception('\n'.join([
            'Extensão não conhecida para o arquivo:',
            caminho,
            'E mimetype:',
            mime,
            ' Algumas possibilidades são:', ] +
            ["    '{}': '{}',".format(mime, ext)
             for ext in mimetypes.guess_all_extensions(mime)] +
            ['Atualize o código do dicionário EXTENSOES!']
        )) from e


def migrar_docs_por_ids(tipo):
    for campo, base_origem, base_destino in DOCS[tipo]:
        print('#### Migrando {} de {} ####'.format(campo, tipo.__name__))

        dir_origem, nome_origem = os.path.split(em_media(base_origem))
        pat = re.compile('^{}$'.format(nome_origem.format('(\d+)')))

        if not os.path.isdir(dir_origem):
            print('  >>> O diretório {} não existe! Abortado.'.format(
                dir_origem))
            continue

        for arq in os.listdir(dir_origem):
            match = pat.match(arq)
            if match:
                origem = os.path.join(dir_origem, match.group(0))
                id = match.group(1)
                extensao = get_extensao(origem)
                destino = base_destino.format(id, extensao)
                mover_documento(origem, destino)

                # associa documento ao objeto
                try:
                    obj = tipo.objects.get(pk=id)
                    setattr(obj, campo, destino)
                    obj.save()
                except tipo.DoesNotExist:
                    msg = '  {} (pk={}) não encontrado para documento em [{}]'
                    print(msg.format(
                        tipo.__name__, id, destino))


def desconecta_sinais_indexacao():
    post_save.disconnect(save_texto, NormaJuridica)
    post_save.disconnect(save_texto, DocumentoAcessorio)
    post_save.disconnect(save_texto, MateriaLegislativa)
    post_delete.disconnect(delete_texto, NormaJuridica)
    post_delete.disconnect(delete_texto, DocumentoAcessorio)
    post_delete.disconnect(delete_texto, MateriaLegislativa)


def conecta_sinais_indexacao():
    post_save.connect(save_texto, NormaJuridica)
    post_save.connect(save_texto, DocumentoAcessorio)
    post_save.connect(save_texto, MateriaLegislativa)
    post_delete.connect(delete_texto, NormaJuridica)
    post_delete.connect(delete_texto, DocumentoAcessorio)
    post_delete.connect(delete_texto, MateriaLegislativa)


def migrar_documentos():
    # precisamos excluir os sinais de post_save e post_delete para não que o
    # computador não trave com a criação de threads desnecessárias
    desconecta_sinais_indexacao()

    # aqui supomos que uma pasta chamada sapl_documentos está em MEDIA_ROOT
    # com o conteúdo da pasta de mesmo nome do zope
    # Os arquivos da pasta serão movidos para a nova estrutura e a pasta será
    # apagada
    migrar_docs_logo()
    for tipo in [
        Parlamentar,
        MateriaLegislativa,
        DocumentoAcessorio,
        NormaJuridica,
        SessaoPlenaria,
        Proposicao,
        DocumentoAdministrativo,
    ]:
        migrar_docs_por_ids(tipo)

    sobrando = [os.path.join(dir, file)
                for (dir, _, files) in os.walk(em_media('sapl_documentos'))
                for file in files]
    if sobrando:
        print('\n#### Encerrado ####\n\n'
              '{} documentos sobraram sem ser migrados!!!'.format(
                  len(sobrando)))
        for doc in sobrando:
            print('  {}'. format(doc))
            #
    # reconexão dos sinais desligados no inicio da migração de documentos
    conecta_sinais_indexacao()
