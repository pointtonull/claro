#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import browser
from os import environ
from debug import debug
import re

rc_file = environ["HOME"] + "/.claro"
"""Este programa lee el archivo ~/.claro que debe ser un CSV de formato:
usuario;numero;pin

Se aceptan multiples registros."""

class CLARO:
    def __init__(self):
        self.browser = browser.get_browser()
        self._login_form = None


    def login(self, numero, pin):
        url = ("""https://individuos.claro.com.ar""")

        if self._login_form is None:
            debug("Consiguiendo un formulario")
            self._login_form = self.browser.get_forms(url, cache=1000)[0]

        self._login_form["_58_login"] = numero
        self._login_form["_58_password"] = pin

        error = self._login_form.submit()
        if "Bienvenido"in error[1]:
            return False
        else:
            return error


    def get_saldo(self, numero, pin):
        self.login(numero, pin)

        url_saldo = ("""https://individuos.claro.com.ar/web/guest/"""
            """saldos-y-consumos""")

        html = self.browser.get_html(url_saldo)
        regex = (r'Saldo Prepago Recarga.*?\$.*?(\d+.\d+).*?'
            r'Saldo Prepago Promocional.*?\$.*?(\d+.\d+).*?'
            r'Saldo Prepago Total.*?\$.*?(\d+.\d+)')

        try:
            res = re.search(regex, html)
            salida = "%s + %s = %s" % (res.group(1), res.group(2), res.group(3))
        except AttributeError:
#            self.browser.show()
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
