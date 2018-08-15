#alarms_sent = set()

def send_alarm(what,msg,logger):

    #if what in alarms_sent:
    #    return

    #alarms_sent.add(what)

    # add signature
    import socket

    msg += ""

    #ALARM_EMAIL = "cernbox-admins@cern.ch"
    ALARM_EMAIL = "georgios.alexandropoulos@cern.ch"

    try:
        logger.warning("ALARM: sending alarm to %s: %s %s",ALARM_EMAIL,what,msg)

        #if not config.ALARM_EMAIL:
        #    logging.warning("sending alarms disabled (no ALARM_EMAIL)")
        #    return

        import smtplib
        fromaddr='cernbox-admins@cern.ch'
        toaddrs=[ALARM_EMAIL]
        email = ("From: %s\r\nTo: %s\r\nSubject: smashbox fail alarm : %s\r\n\r\n" % (fromaddr, ", ".join(toaddrs), what))
        email += what + ': ' + msg
        server = smtplib.SMTP('localhost')
        #server.set_debuglevel(1)
        server.sendmail(fromaddr, toaddrs, email)
        server.quit()
    except Exception,x:
        logger.critical("problem sending alarm: %s %s",what,str(x))
        alarms_sent.remove(what)


