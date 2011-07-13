#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import browser
from os import environ
from debug import debug
import re

rc_file = environ["HOME"] + "/.claro"
URL_LOGIN = ("http://www.servicios.claroargentina.com/AutogestionCore2006/"
    "servlet/Controller?EVENT=WELCOMEMAS&OFLINE")
URL_SALDO = ("http://www.servicios.claroargentina.com/AutogestionCore2006/"
    "servlet/Controller?EVENT=DATOS_FACTURA")

"""Este programa lee el archivo ~/.claro que debe ser un CSV de formato:
usuario;numero;pin

Se aceptan multiples registros.

Como la nueva página de servicios claro está fallando mucho (la mayor parte del
tiempo no muestra el saldo disponible) estamos evaluando la posibilidad de
que el script consulte en la vieja página cuando los datos no estén disponibles
en la nueva.

http://www.servicios.claroargentina.com/AutogestionCore2006/servlet/Controller
"""

class CLARO:
    def __init__(self):
        self.browser = browser.Browser()
        self._login_form = None


    def login(self, numero, pin):

        if self._login_form is None:
            debug("Consiguiendo un formulario")
            forms = self.browser.get_forms(URL_LOGIN)
            html = self.browser.get_html()
            if forms:
                self._login_form = forms[0]
            elif "En este momento no podemos atender tu consulta." in html:
                return False
            else:
                self.browser.show()


        self._login_form["loginNumber"] = numero
        self._login_form["password"] = pin

        error = self._login_form.submit()
        if "Bienvenido" in error[1]:
            return False
        else:
            return error


    def get_saldo(self, numero, pin):
        self.login(numero, pin)

        html = self.browser.get_html(URL_SALDO)

        regex = (r'''(?six)
            class="txt05".*?>.*?saldo.*?prepaga.*?\$\s*(\d*,\d*)
            ''')

        try:
            res = re.search(regex, html)
            prepago = "%s" % (res.group(1))
        except AttributeError:
            self.browser.show()
            return "Error"
        else:
            prepago = prepago.replace(",", ".")

        regex = (r'''(?six)
            class="txt05".*?>.*?pesos.*?libres.*?disponibles.*?\$\s*(\d*,\d*)
            ''')
        
        try:
            res = re.search(regex, html)
            libres = "%s" % (res.group(1))
        except AttributeError:
            libres = "0.0"
        else:
            libres = libres.replace(",", ".")

        total = float(libres) + float(prepago)

        return "%s + %s = %.2f" % (libres, prepago, total)



def main():
    claro = CLARO()

    users = [line.strip().split(";")
        for line in open(rc_file).readlines()]

    for user in users:
        print "%s: %s" % (user[0], claro.get_saldo(user[1], user[2]))


if __name__ == "__main__":
    exit(main())
