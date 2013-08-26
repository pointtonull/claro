#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from collections import defaultdict
from optparse import OptionParser
import logging
import os
import re
import sys

from BeautifulSoup import BeautifulSoup

from litebrowser import Browser

APP_NAME = "claro"
LOG_FILE = os.path.expanduser("~/.%s.log" % APP_NAME)
CONFIG_FILE = os.path.expanduser("~/.%s" % APP_NAME)
VERBOSE = 20

class UsageError(RuntimeError):
    pass

def get_depth():
    """
    Returns the current recursion level. Nice to look and debug
    """
    def exist_frame(number):
        """
        True if frame number exists
        """
        try:
            if sys._getframe(number):
                return True
        except ValueError:
            return False

    maxn = 1
    minn = 0

    while exist_frame(maxn):
        minn = maxn
        maxn *= 2

    middle = (minn + maxn) / 2

    while minn < middle:
        if exist_frame(middle):
            minn = middle
        else:
            maxn = middle

        middle = (minn + maxn) / 2

    return max(minn - 4, 0)


def ident(func, identation="  "):
    """
    Decorates func to add identation prior arg[0]
    """
    def decorated(message, *args, **kwargs):
        newmessage = "%s%s" % (identation * (get_depth() - 1), message)
        return func(newmessage, *args, **kwargs)
    return decorated


def get_options():
    """
    Parse the arguments
    """
    # Instance the parser and define the usage message
    optparser = OptionParser(usage="""
    %prog [-vqld]""", version="%prog .1")

    # Define the options and the actions of each one
    optparser.add_option("-v", "--verbose", action="count", dest="verbose",
        help="Increment verbosity")
    optparser.add_option("-q", "--quiet", action="count", dest="quiet",
        help="Decrement verbosity")
    optparser.add_option("-l", "--log", help=("Uses the given log file "
        "inteast of the default"), action="store", dest="logfile")
    optparser.add_option("-i", "--insecure", help=("Will raise exceptions."),
        action="store_true", dest="insecure")
    optparser.add_option("-d", "--dummy", help=("Will execute a dummy test."),
        action="store_true", dest="dummy")

    # Define the default options
    optparser.set_defaults(verbose=0, quiet=0, logfile=LOG_FILE,
        conffile="", dummy=False, insecure=False)

    # Process the options
    options, args = optparser.parse_args()
    return options, args


class Claro:
    def __init__(self, account):
        self.account = account
        self.browser = Browser()


    def login(self):
        form = self.browser.get_forms("https://individuos.claro.com.ar")[1]
        form["login"] = self.account[0]
        form["password"] = self.account[1]
        form.submit()


    def get_saldos(self):
        saldos = {}
        html = self.browser.get_html("web/guest/saldos-y-consumos1")
        regexs = {
            "Abono fijo": r'''
                (?xs)Saldo\ del\ Abono:.*?\$
                (?P<saldo> (?:\d+,)?\d+ ).*?Llevás\ consumidos\ \$
                (?P<consumido> (?:\d+,)?\d+ ).*?
                (?P<total> \d*,\d* ).*?Per.+?odo\ actual.*?
                (?P<vencimiento> \d+/\d+/\d+ )
                ''',
            "Paquete de datos": r'''
                (?xs)Saldo\ de\ Paquetes.*?Te\ quedan\ 
                (?P<saldo> \d+? )\ MB\ de\ tu\ paquete\ de\ 
                (?P<total> \d+ )\ MB\..*?Vence\ el\ 
                (?P<vencimiento> \d+/\d+/\d+ )
                ''',
            "Paquete de sms": r'''
                (?xs).*?Te\ quedan\ 
                (?P<saldo> \d+ )\ SMS\ de\ tu\ paquete\ de\ 
                (?P<total> \d+ )\ SMS\..*?Vence\ el\ +
                (?P<vencimiento> \d+/\d+/\d+ )
                ''',
            "SMS Promocionales": r'''
                (?xs)SMS\ Promocionales.*?Tenés\ .*?
                (?P<saldo> \d+ ).*?SMS\ disponibles\ hasta\ el\ 
                (?P<vencimiento> \d+/\d+/\d+ )
                ''',
            "Crédito prepago congelado": r'''
                (?xs)Crédito\ de\ Recarga.*?Crédito\ Congelado.*?
                    Saldo.*?Vencimiento.*?\$
                (?P<saldo> \d+,\d+ ).*?
                (?P<vencimiento> \d+/\d+/\d+ ).*?Última\ recarga.*?
                (?P<ultima_recarga> \d+/\d+/\d+ )
                ''',
            "Crédito prepago vigente": r'''
                (?xs)Crédito\ de\ Recarga.*?Recarga.*?\$
                (?P<saldo> \d+,\d+ ).*?
                (?P<vencimiento> \d+/\d+/\d+ )
                ''',
            "Crédito prepago promocional": r'''
                (?xs)Crédito\ de\ Recarga.*?Promocional.*?\$
                (?P<saldo> \d+,\d+ ).*?
                (?P<vencimiento> \d+/\d+/\d+ )
                ''',
            "Crédito de recarga": r'''
                (?xs)Crédito\ de\ Recarga.*?Última\ recarga.*?
                (?P<ultima_recarga> \d+/\d+/\d+ )
                '''
        }
        for title, regex in regexs.items():
            match = re.search(regex, html)
            if match:
                saldos[title] = match.groupdict()
        return saldos


    def get_circulo_opciones(self):
        self.browser.go("web/guest/consultar-claro-club")
        self.browser.get_forms()[0].submit()
        soup = BeautifulSoup(self.browser.get_html())
        opciones = []
        regex = re.compile(r"""(?xs) <tr>\ <td.*?>
            (?P<descripcion>(?P<cantidad>\d+).*?)  </td>\ <td.*?>
            (?P<puntos>\d+)                        .*?</td>.*?goSubmit\('
            (?P<codigo>\d+)                        '\)"""
        )
        for table in soup("table", {"class":"tabla tablaGris"}):
            for row in table("tr"):
                rawtext = row.__str__()
                if "goSubmit(" in rawtext and "SMS" in rawtext:
                    match = regex.match(rawtext)
                    opciones.append(match.groupdict())
        return opciones



def main(options, args):
    """The main routine"""
    MOREINFO("\n=== COMENZANDO ejecución ===")
    accounts = [account for account in (line.strip().split("#")[0].split(";")
        for line in open(CONFIG_FILE).readlines())
            if len(account) == 3]
    if len(sys.argv) == 2:

        identificador = sys.argv.pop()
        d_accounts = {
            nombre:(numero, pin)
            for nombre, numero, pin in accounts}
        d_accounts.update({
            numero:(numero, pin)
            for nombre, numero, pin in accounts})
        account = d_accounts[identificador]

    elif len(sys.argv) == 3:

        pin = sys.argv.pop()
        numero = sys.argv.pop()
        account = numero, pin

    else:

        raise UsageError("Se espera como argumento un identificador declarado en la"
            " configuración (~/.claro) o un par número contraseña")

    claro = Claro(account)
    claro.login()
    saldos = claro.get_saldos()
    for title, grupo in sorted(saldos.items()):
        print(title)
        for concepto in sorted(grupo.keys()):
            print "    %s: %s" % (concepto, grupo[concepto])

    MOREINFO("\n=== FINALIZANDO ejecución ===\n")
    return 0


if __name__ == "__main__":
    # == Reading the options of the execution ==
    options, args = get_options()

    VERBOSE = (options.quiet - options.verbose) * 10 + 30
    format_str = "%(message)s"
    logging.basicConfig(format=format_str, level=VERBOSE)
    logger = logging.getLogger()

    DEBUG = ident(logger.debug) # For developers
    MOREINFO = ident(logger.info) # Plus info
    INFO = ident(logger.warning) # Default
    WARNING = ident(logger.error) # Non critical errors
    ERROR = ident(logger.critical) # Critical (will break)

    DEBUG("get_options::options: %s" % options)
    DEBUG("get_options::args: %s" % args)

    DEBUG("Verbose level: %s" % VERBOSE)
    exit(main(options, args))
