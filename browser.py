#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from cStringIO import StringIO
from tempfile import mkdtemp
import mechanize
import cookielib
import os
import time
import urllib2
import webbrowser

#SOME GLOBALS
TEMPDIR = mkdtemp()
HOME = os.environ["HOME"]

#TODO: Add some default presets
DEFAULT = {
    "User-Agent":"Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"
    }
#FIREFOX = {
#    }
#CHROMIUM = {
#    }


#TODO: Add a presets maker wizzard to use your browser settings
#class Real_browser(object):
#    def __init__(self, browser="default"):
#        pass

#TODO: Must Form hederate from mechanize?
class Form(object):
    def __init__(self, parent, form):
        """
        :parent: The Browser instance that will process the submit
        :form: The mechanize instante that manages the form
        """
        self.parent = parent
        self._form = form
        self.names = [control.name for control in self._form.controls]


    def click_request_data(self):
        return self._form.click_request_data()


    def __getitem__(self, y):
        return self._form.__getitem__(y)


    def __setitem__(self, i, y):
        return self._form.__setitem__(i, y)


    def __repr__(self):
        return str(self.names)


    def __str__(self):
        return self._form.__str__()


    def click(self):
        return self._form.click()


    def submit(self, data=None, timeout=None):
        return self.parent.go(self._form.click(), data, timeout)


    def set_all_readonly(self, *args, **kw):
        return self._form.set_all_readonly(*args, **kw)



class Cookies_mngr(cookielib.CookieJar):
    def __init__(self, *args, **kwargs):
        """
        initializes the CookieJar class that implements:
            .add_cookie_header
            .clear
            .clear_expired_cookies
            .clear_session_cookies
            .domain_re
            .dots_re
            .extract_cookies
            .magic_re
            .make_cookies
            .non_word_re
            .quote_re
            .set_cookie
            .set_cookie_if_ok
            .set_policy
            .strict_domain_re
        """

        cookielib.CookieJar.__init__(self)


    def save_cookies(self, filename):
        """
        saves the cookies to a file
        """

    def load_cookies(self, filename):
        """
        loads cookies from a file
        """


class Source_parser:
    def __init__(self):
        """
        Will default to BeatifulSoap becouse its a very fast parser that does a
        really good job with invalid/broken HTML.
        """

        #TODO: Must depend on presets when implementeds
        from BeatifulSoup import BeatifulSoup
        self._parser = BeatifulSoup


    def parse(self, source):
        self.soup = BeatifulSoup(source)




class Cache_mngr(urllib2.BaseHandler):
    def __init__(self, backend=None):
        """
        initializes the backend connection
        """

    def get_html(self, url):
        """
        returns the html and the time it was fetched
        """



class Browser(object):
    def __init__(self, preset=DEFAULT, cookiesmngr=None, cachemngr=None,
        proxiesmngr=None):
        """
        instantes a cookie manager if not given
        instances a cache manager if not given
        instances a proxies manager if not given
        instances a html
        instances a urllib2 opener for private use
        """

        #FIXME: Must depend on presets when implementeds
        self.cache = cachemngr or Cache_mngr()
        self.cookies = cookiesmngr or Cookies_mngr()
        self.proxies = proxiesmngr or urllib2.ProxyHandler()
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookies),
            self.proxies, self.cache)
        self.opener.addheaders = [('User-agent', preset["User-Agent"])]


    def config(self):
        """
        getter and setter to the self._config dict
        """

    def reload(self):
        """
        reload the current url and update states

        return result
        """

    def show(self, url=None, openon=None):
        """
        open a copy of the current html in a webbrowser
        """

        if url:
            self.go(url)
        temppath = "%s/%d.html" % (TEMPDIR, time.time())
        tempfile = open(temppath, "w")
        tempfile.write(self.get_html())
        tempfile.close()

        if not openon:
            return webbrowser.open(temppath)
        else:
            return webbrowser.GenericBrowser(openon).open(temppath)


    def go(self, url, data=None, timeout=None):
        """
        requests the html and updates the statuses

        returns the opener msg
        """
        self._last_req = self.opener.open(url, data, timeout)
        return self._update_status()


    def _update_status(self, request=None):
        """
        """
        request = request or self._last_req
        self._code = request.code
        self._url = request.url
        self._msg = request.msg
        self._headers = request.headers
        self._html = request.read()
        return self._msg


    def get_html(self, url=None, data=None, timeout=None):
        """
        returns the html
        """
        if url:
            self.go(url, data, timeout)
        return self._html


    def get_title(self, url=None, data=None, timeout=None):
        """
        returns the title
        """
        if url:
            self.go(url, data, timeout)
        return self._title


    def get_code(self, url=None, data=None, timeout=None):
        """
        returns the error code
        """
        if url:
            self.go(url, data, timeout)
        return self._code


    def get_url(self):
        """
        returns the current url
        """
        return self._url


    def get_forms(self, url=None, data=None, timeout=None):
        """
        return the forms
        """
        if url:
            self.go(url, data, timeout)
        
        fifo = StringIO()
        fifo.writelines(self.get_html())
        fifo.seek(0)
        forms = mechanize.ParseFile(fifo, self.get_url(),
            backwards_compat=False) 
        return [Form(self, form) for form in forms]


def main():
    #TODO: Implement a shell like language for web scripting
    browser = Browser()
    print(browser.go("https://joindiaspora.com/users/sign_in"))
    forms = browser.get_forms()
    form = forms[0]
    form["user[username]"] = raw_input("User: ")
    form["user[password]"] = raw_input("Password: ")
    print(form.submit())
    forms = browser.get_forms()
    form = forms[2]
    form.set_all_readonly(False)
    form["status_message[public]"] = "true"
    form["status_message[text]"] = raw_input("Message: ")
    print(form.submit())
    browser.show()


if __name__ == "__main__":
    exit(main())
