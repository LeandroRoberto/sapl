from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Fieldset, Layout
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
import sapl
from crispy_layout_mixin import form_actions
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE

from .models import CasaLegislativa


class CasaLegislativaTabelaAuxForm(ModelForm):

    class Meta:

        model = CasaLegislativa
        fields = ['codigo',
                  'nome',
                  'sigla',
                  'endereco',
                  'cep',
                  'municipio',
                  'uf',
                  'telefone',
                  'fax',
                  'logotipo',
                  'endereco_web',
                  'email',
                  'informacao_geral']

        widgets = {
            'uf': forms.Select(attrs={'class': 'selector'}),
            'cep': forms.TextInput(attrs={'class': 'cep'}),
            'telefone': forms.TextInput(attrs={'class': 'telefone'}),
            'fax': forms.TextInput(attrs={'class': 'telefone'}),
            'logotipo': sapl.utils.ImageThumbnailFileInput,
            'informacao_geral': forms.Textarea(
                attrs={'id': 'texto-rico'})
        }

    def clean_logotipo(self):
        logotipo = self.cleaned_data.get('logotipo', False)
        if logotipo:
            if logotipo.size > MAX_IMAGE_UPLOAD_SIZE:
                raise ValidationError("Imagem muito grande. ( > 2mb )")
        return logotipo

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('codigo', 2),
             ('nome', 5),
             ('sigla', 5)])

        row2 = crispy_layout_mixin.to_row(
            [('endereco', 8),
             ('cep', 4)])

        row3 = crispy_layout_mixin.to_row(
            [('municipio', 10),
             ('uf', 2)])

        row4 = crispy_layout_mixin.to_row(
            [('telefone', 6),
             ('fax', 6)])

        row5 = crispy_layout_mixin.to_row(
            [('logotipo', 12)])

        row6 = crispy_layout_mixin.to_row(
            [('endereco_web', 12)])

        row7 = crispy_layout_mixin.to_row(
            [('email', 12)])

        row8 = crispy_layout_mixin.to_row(
            [('informacao_geral', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Dados Básicos'),
                row1,
                row2,
                row3,
                row4,
                row5,
                HTML("""
  <div class="col-md-12">
    {% if not form.fotografia.errors and form.fotografia.value %}
    <img class="img-responsive" width="225" height="300"
         src="{{ MEDIA_URL }}{{ form.logotipo.value }}">
         <br />
    <input type="submit"
           name="remover"
           id="remover"
           class="btn btn-warning"
           value="Remover Logo"/>
     {% endif %}
   </div>"""),
                row6,
                row7,
                row8,
                form_actions()
            )
        )
        super(CasaLegislativaTabelaAuxForm, self).__init__(*args, **kwargs)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(
                                attrs={
                                 'class': 'form-control', 'name': 'username'}))
    password = forms.CharField(label="Password", max_length=30,
                               widget=forms.PasswordInput(
                                attrs={
                                 'class': 'form-control', 'name': 'password'}))
