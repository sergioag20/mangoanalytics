#Views for providers

import datetime
from django.utils.timezone import utc
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from tarifica import forms
from tarifica.tools.asteriskMySQLManager import AsteriskMySQLManager
from tarifica.models import *
from django.forms.formsets import formset_factory

def createProvider(request, asterisk_id):
    provider = get_object_or_404(Provider, asterisk_id = asterisk_id)

    if request.method == 'POST': # If the form has been submitted...
        form = forms.createProvider(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            provider.name = form.cleaned_data['name']
            provider.monthly_cost = form.cleaned_data['monthly_cost']
            provider.period_end = form.cleaned_data['period_end']
            provider.payment_type = PaymentType.objects.get(id=form.cleaned_data['payment_type'])
            provider.channels = form.cleaned_data['channels']
            provider.is_configured = True
            provider.save()
            return HttpResponseRedirect('/tarifica/setup') # Redirect after POST
    else:
        form = forms.createProvider() # An unbound form

    return render(request, 'tarifica/providerCreate.html', {
        'form': form,
        'provider': provider
    })

def getProvider(request, provider_id):
	provider = get_object_or_404(Provider, id = provider_id)
	destination_groups = DestinationGroup.objects.filter(provider = provider)
	bundles = Bundle.objects.filter(destination_group__in = destination_groups)
	return render(request, 'tarifica/providerGet.html', {
        'provider': provider,
        'destination_groups': destination_groups,
        'bundles': bundles,
    })

def updateProvider(request, provider_id):
    provider = get_object_or_404(Provider, id = provider_id)

    if request.method == 'POST': # If the form has been submitted...
        form = forms.createProvider(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            provider.name = form.cleaned_data['name']
            provider.monthly_cost = form.cleaned_data['monthly_cost']
            provider.period_end = form.cleaned_data['period_end']
            provider.payment_type = PaymentType.objects.get(id=form.cleaned_data['payment_type'])
            provider.channels = form.cleaned_data['channels']
            provider.is_configured = True
            provider.save()
            return HttpResponseRedirect('/tarifica/setup') # Redirect after POST
    else:
        form = forms.createProvider(initial=
        {'name': provider.name,
         'monthly_cost': provider.monthly_cost,
         'period_end': provider.period_end,
         'payment_type': provider.payment_type,
         'channels': provider.channels,
        }
        )# An unbound form

    return render(request, 'tarifica/providerUpdate.html', {
        'form': form,
        'provider': provider
    })

def deleteProvider(request, provider_id):
    provider = get_object_or_404(Provider, id = provider_id)
    provider.delete()
    return HttpResponseRedirect('/tarifica/setup')