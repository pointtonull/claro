#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from optparse import OptionParser
import logging
import os
import re
import sys
import time

from get_saldo import Claro

APP_NAME = "claro"
LOG_FILE = os.path.expanduser("~/.%s.log" % APP_NAME)
CONFIG_FILE = os.path.expanduser("~/.%s" % APP_NAME)
VERBOSE = 20


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


def auto_trade(phone_number, password, dummy=False):
    claro = Claro((phone_number, password))
    claro.login()

    saldos = claro.get_saldos()
    sms_saldo = 0
    for cat in saldos:
        if "sms" in cat.lower():
            sms_saldo += int(saldos[cat]["saldo"])

    MOREINFO("Saldo de sms: %d" % sms_saldo)
    if sms_saldo >= 20:
        INFO("Ya tiene %d SMS disponibles, no se cargarán más." % sms_saldo)
        return

    opciones = claro.get_circulo_opciones()
    if not opciones:
        INFO("No tiene opciones de canje por paquetes SMS.")
        return

    opcion = sorted([(
        abs(
            int(op["cantidad"]) + sms_saldo - 30),
            int(op["cantidad"]),
            op["descripcion"],
            op["codigo"],
        )
        for op in opciones])[0]

    INFO("Seleccionado: %s" % opcion[-2])

    # Ejecución de la selección
    form = claro.browser.get_forms()[0]
    form.set_all_readonly(False)
    form["selectedAward"] = opcion[-1]
    form["event"] = "confirmation"
    if dummy:
        WARNING("No se ejecuta la acción en modo dummy.")
    else:
        form.submit()
        form = claro.browser.get_forms()[0]
        form.submit()


def secure_proccess(acounts):
    """accounts -> failed_acounts"""
    errors = []
    for acount in acounts:
        username, phone_number, password = acount
        INFO("\n%s - Procesando %s: %s - %s" % (time.ctime(), username, phone_number,
            password))
        try:
            auto_trade(phone_number, password, dummy=options.dummy)
        except:
            if options.insecure:
                raise
            WARNING("Error realizando la operación, operación reprogramada.")
            errors.append(acount)
        else:
            INFO("Operación realizada con éxito")
    return errors


def main(options, args):
    """The main routine"""
    MOREINFO("\n=== COMENZANDO ejecución ===")
    acounts = [acount for acount in (line.strip().split("#")[0].split(";")
        for line in open(CONFIG_FILE).readlines())
            if len(acount) == 3]
    
    wait = 90
    for attempt in range(20):
        acounts = secure_proccess(acounts)
        if acounts:
            MOREINFO("\nHAY CUENTAS SIN PROCESAR")
            MOREINFO("Esperando %d segundos para evitar errores 403" % wait)
            time.sleep(wait)
            wait *= 1.5
    if acounts:
        ERROR("\nLas siguientes cuentas no han podido ser procesadas:")
        for acount in acounts:
            ERROR(acount)

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
