# -*- coding: utf-8 -*-

#!/usr/bin/env python2.7
from asteriskMySQLManager import AsteriskMySQLManager
from datetime import datetime, timedelta, date
from assignCallCost import CallCostAssigner
from digester import Digester
import subprocess
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def saveImportFinishStatus():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "UPDATE tarifica_userinformation \
        SET tarifica_userinformation.is_first_import_finished = %s"
    am.cursor.execute(sql, (True,))
    am.db.commit()
    return am.db.close()

def saveImportResults(calls_saved, calls_not_saved):
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "INSERT INTO tarifica_importresults(calls_saved, calls_not_saved) \
        VALUES(%s, %s)"
    am.cursor.execute(sql, (calls_saved, calls_not_saved))
    am.db.commit()
    return am.db.close()

def deleteAllCalls():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "DELETE FROM tarifica_call"
    am.cursor.execute(sql, ())
    am.db.commit()
    return am.db.close()
        
def deleteAllUnconfiguredCalls():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "DELETE FROM tarifica_unconfiguredcall"
    am.cursor.execute(sql, ())
    am.db.commit()
    return am.db.close()

def deleteAllUserDailyDetail():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "DELETE FROM tarifica_userdailydetail"
    am.cursor.execute(sql, ())
    am.db.commit()
    return am.db.close()

def deleteAllUserDestinationDetail():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "DELETE FROM tarifica_userdestinationdetail"
    am.cursor.execute(sql, ())
    am.db.commit()
    return am.db.close()

def deleteAllUserDestinationNumberDetail():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "DELETE FROM tarifica_userdestinationnumberdetail"
    am.cursor.execute(sql, ())
    am.db.commit()
    return am.db.close()

def deleteAllProviderDailyDetail():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "DELETE FROM tarifica_providerdailydetail"
    am.cursor.execute(sql, ())
    am.db.commit()
    return am.db.close()

def deleteAllProviderDestinationDetail():
    am = AsteriskMySQLManager()
    am.connect('nextor_tarificador')
    sql = "DELETE FROM tarifica_providerdestinationdetail"
    am.cursor.execute(sql, ())
    am.db.commit()
    return am.db.close()

# This file processes two month's worth of data, using assignCallCost and Digester
# We go six months back... back in time!

today = date.today()
six_months_back = today - timedelta(days = 190) # Half a year
cca = CallCostAssigner()
dig = Digester()
calls_saved = 0
calls_not_saved = 0
testRun = False

if len(sys.argv) > 1:
    if sys.argv[1] == '--testrun':
        testRun = True
#Comenzamos borrando tooooodo
if testRun:
        deleteAllUnconfiguredCalls()
else:   
    deleteAllCalls()
    deleteAllUnconfiguredCalls()
    deleteAllUserDailyDetail()
    deleteAllUserDestinationDetail()
    deleteAllUserDestinationNumberDetail()
    deleteAllProviderDailyDetail()
    deleteAllProviderDestinationDetail()
print "Deleted all previous data."

while six_months_back != today:
    print "Digesting data from", six_months_back.strftime('%Y-%m-%d')
    
    # Assign call costs to selected day
    result = cca.getDailyAsteriskCalls(six_months_back)
    calls_saved += result['total_calls_saved']
    calls_not_saved += result['total_calls_not_saved']
    
    if not testRun:    
        dig.saveUserDailyDetail(six_months_back)
        dig.saveUserDestinationDetail(six_months_back)
        dig.saveUserDestinationNumberDetail(six_months_back)
        dig.saveProviderDailyDetail(six_months_back)
        dig.saveProviderDestinationDetail(six_months_back)

    six_months_back = six_months_back + timedelta(days = 1)

print saveImportFinishStatus()
if testRun:
    saveImportResults(calls_saved, calls_not_saved)
    print "----------------------------------------"
    print "Testrun finished."
else:
    print "----------------------------------------"
    print "Import status set as finished."