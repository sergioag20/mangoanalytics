#Views for providers

import datetime
from django.utils.timezone import utc
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from tarifica.tools.asteriskMySQLManager import AsteriskMySQLManager
from tarifica.models import *
from django.forms.formsets import formset_factory

def setup(request):
    a_mysql_m = AsteriskMySQLManager()
    users = a_mysql_m.getUserInformation()
    for u in users:
        if u['name']:
            try:
                e = Extension.objects.get(name = u['name'])
            except Extension.DoesNotExist:
                e = Extension(
                    name = u['name'],
                    extension_number = u['extension'],
                    )
                e.save()
            except Extension.MultipleObjectsReturned:
                print "extensiones repetidas!"
    trunks = a_mysql_m.getTrunkInformation()
    for x in trunks:
        if x['name']:
            try:
                e = Provider.objects.get(asterisk_id = x['trunkid'])
            except Provider.DoesNotExist:
                p = Provider(
                    asterisk_id = x['trunkid'],
                    asterisk_name = x['name'],
                    provider_type = x['tech'],
                    asterisk_channel_id = x['channelid']
                    )
                p.save()
            except Provider.MultipleObjectsReturned:
                print "troncales repetidas!"
    providers_not_configured = Provider.objects.filter(is_configured=False).order_by('asterisk_name')
    providers_configured = Provider.objects.filter(is_configured=True).order_by('name')
    bundles = Bundle.objects.all().order_by('name')
    locales = DestinationGroup.objects.all()
    return render(request, 'tarifica/setup.html', {
        'not_configured' : providers_not_configured,
        'configured' : providers_configured,
        'bundles' : bundles,
        'locales' : locales,
    })

def trunks(request):
    a_mysql_m = AsteriskMySQLManager()
    users = a_mysql_m.getUserInformation()
    for u in users:
        if u['name']:
            try:
                e = Extension.objects.get(name = u['name'])
            except Extension.DoesNotExist:
                e = Extension(
                    name = u['name'],
                    extension_number = u['extension'],
                    )
                e.save()
            except Extension.MultipleObjectsReturned:
                print "extensiones repetidas!"
    trunks = a_mysql_m.getTrunkInformation()
    for x in trunks:
        if x['name']:
            try:
                e = Provider.objects.get(asterisk_id = x['trunkid'])
            except Provider.DoesNotExist:
                p = Provider(
                    asterisk_id = x['trunkid'],
                    asterisk_name = x['name'],
                    provider_type = x['tech'],
                    asterisk_channel_id = x['channelid']
                    )
                p.save()
            except Provider.MultipleObjectsReturned:
                print "troncales repetidas!"
    providers_not_configured = Provider.objects.filter(is_configured=False).order_by('asterisk_name')
    providers_configured = Provider.objects.filter(is_configured=True).order_by('name')
    bundles = Bundle.objects.all().order_by('name')
    locales = BaseTariff.objects.all()
    return render(request, 'tarifica/dashboardtroncales.html', {
                  'not_configured' : providers_not_configured,
                  'configured' : providers_configured,
                  'bundles' : bundles,
                  'locales' : locales,
                  })

def realtime(request):
    import subprocess, re
    today = datetime.datetime.utcnow().replace(tzinfo=utc)
    #process = subprocess.check_output(["asterisk","-rx core show channels verbose"])
    process ='Channel              Context              Extension        Prio State   Application  Data                      CallerID        Duration Accountcode PeerAccount BridgedTo\nIP/469-000002aa     macro-dialout-trunk  s                  19 Up      Dial         SIP/Nextor/525555543001,3 469             00:00:25                         SIP/Nextor-000002ab\nSIP/464-000002ac     macro-dialout-trunk  s                  19 Ring    Dial         SIP/Nextor/525555458610,3 464             00:00:13                         (None)\nSIP/4680-000002b0    from-internal        555                 3 Up      Wait         1                         4680            00:00:00                         (None)\nSIP/Nextor-000002ab  from-pstn                                1 Up      AppDial      (Outgoing Line)           755543001       00:00:25                         SIP/469-000002aa\nSIP/Nextor-000002af  from-pstn            752909139           1 Down    AppDial      (Outgoing Line)           752909139       00:00:09                         (None)\nSIP/Nextor-000002ad  from-pstn            755458610           1 Down    AppDial      (Outgoing Line)           755458610       00:00:13                         (None)\nSIP/470-000002ae     macro-dialout-trunk  s                  19 Ring    Dial         SIP/Nextor/525552909139,3 470             00:00:09                         (None)\n\n7 active channels\n4 active calls\n412 calls processed'
    data = re.split("\n+", process)[1:-4]
    processed_data = [re.split(" +", d, 9) for d in data if d[6] ]
    data = [
        [ d[7], "algo", re.split("/", d[6])[1],re.split(",", re.split("/", d[6])[2])[0], d[8] ] 
        for d in processed_data if re.search("/",d[6])
        ]
    for d in data:
        t1 = datetime.datetime.strptime(d[4], "%H:%M:%S")
        print t1
        timedelta = datetime.timedelta(hours=t1.hour, minutes=t1.minute, seconds=t1.second)
        t = today - timedelta
        print t
        d.append(t.time().strftime("%H:%M:%S"))
        provider = Provider.objects.get(Provider, asterisk_name = d[2])
        destination_groups = DestinationGroup.objects.filter(provider = provider)
        for d in destination_groups:
            try:
                pos = d[3].index(d.prefix)
            except ValueError,e :
                post = None
            if pos is None or pos != 0:
                ""
    return render(request, 'tarifica/realtime.html', {
              'data' : data,
              })

def dashboard(request):
    from django.db import connection, transaction
    cursor = connection.cursor()
    end_date = datetime.datetime.utcnow().replace(tzinfo=utc)
    start_date = datetime.date(end_date.year,end_date.month, 1)
    provider_daily_costs = []
    total_cost = 0
    providers = Provider.objects.filter(is_configured=True)
    for prov in providers:
        detail = ProviderDailyDetail.objects.filter(date__range=(start_date,end_date)).filter(provider = prov)
        provider_total_cost = 0
        for e in detail:
            provider_total_cost = e.cost + provider_total_cost
        provider_daily_costs.append((prov,provider_total_cost))
        total_cost += provider_total_cost
    cursor.execute('SELECT tarifica_providerdestinationdetail.id, SUM(tarifica_providerdestinationdetail.cost) AS cost, tarifica_destinationgroup.name, tarifica_providerdestinationdetail.destination_group_id AS destid\
        FROM tarifica_providerdestinationdetail \
        LEFT JOIN tarifica_destinationgroup \
        ON tarifica_providerdestinationdetail.destination_group_id = tarifica_destinationgroup.id \
        WHERE date > %s AND date < %s GROUP BY destination_group_id ORDER BY SUM(cost) DESC',
        [start_date,end_date])
    locales = dictfetchall(cursor)[:3]
    cursor.execute('SELECT tarifica_userdailydetail.id, SUM(tarifica_userdailydetail.cost) AS cost, tarifica_extension.name, tarifica_extension.extension_number, tarifica_userdailydetail.extension_id AS extid \
        FROM tarifica_userdailydetail \
        LEFT JOIN tarifica_extension\
        ON tarifica_userdailydetail.extension_id = tarifica_extension.id \
        WHERE date > %s AND date < %s GROUP BY extension_id ORDER BY SUM(cost) DESC',
        [start_date,end_date])
    extensions = dictfetchall(cursor)[:3]
    return render(request, 'tarifica/generaldashboard.html', {
              'total_cost' : total_cost,
              'provider_daily_costs' : provider_daily_costs,
              'locales' : locales,
              'extensions' : extensions
              })

def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]