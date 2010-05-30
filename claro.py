#!/usr/bin/env python
#-*- coding: UTF-8 -*-
from browser import BROWSER
from os import environ
from debug import debug
import re

rc_file = environ["HOME"] + "/.claro"
"""Este programa lee el archivo ~/.claro que debe ser un CSV de formato:
usuario;numero;pin

Se aceptan multiples registros."""

class CLARO:
    def __init__(self):
        self.browser = BROWSER()
        self._login_form = None


    def login(self, numero, pin):
        url = """http://www.servicios.claroargentina.com/AutogestionCore2006/servlet/Controller?EVENT=WELCOMEMAS"""
        
        if self._login_form is None:
            self._login_form = self.browser.get_forms(url, cache=1000)[0]

        self._login_form["loginNumber"] = numero
        self._login_form["password"] = pin

        return self._login_form.submit()


    def get_saldo(self, numero, pin):
        self.login(numero, pin)
        
        url_saldo = """http://www.servicios.claroargentina.com/AutogestionCore2006/servlet/Controller?EVENT=DATOS_FACTURA"""

        html = self.browser.get_html(url_saldo)

        try:
            salida = re.search("""(?s)Saldo.*?Prepaga.*?\$.*?(\d*,\d*)""", html).group(1)
        except AttributeError:
            return "Error"
        else:
            return salida.replace(",", ".")


def main():
    claro = CLARO()

    users = [line.strip().split(";")
        for line in open(rc_file).readlines()]

    for user in users:
        print "%s: %s" % (user[0], claro.get_saldo(user[1], user[2]))


if __name__ == "__main__":
    exit(main())
