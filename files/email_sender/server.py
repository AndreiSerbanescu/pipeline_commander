# from smtplib import SMTP_SSL, SMTP
#
# def start_server():
#     with SMTP(host='localhost', port=1025) as server:
#         server.noop()
#         server.sendmail(from_addr="test@test.com", to_addrs="andreis120@gmail.com", msg="this is a test email", mail_options=())

import smtpd
import aiosmtpd
from aiosmtpd.handlers import Proxy
import asyncore


class Devnull:
    def write(self, msg): pass
    def flush(self): pass


DEBUGSTREAM = Devnull()
NEWLINE = '\n'
COMMASPACE = ', '
DATA_SIZE_DEFAULT = 33554432

class ModifiedPureProxy(smtpd.SMTPServer):
    def __init__(self, *args, **kwargs):
        if 'enable_SMTPUTF8' in kwargs and kwargs['enable_SMTPUTF8']:
            raise ValueError("PureProxy does not support SMTPUTF8.")
        super(ModifiedPureProxy, self).__init__(*args, **kwargs)

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        lines = data.split('\n')
        # Look for the last header
        i = 0
        for line in lines:
            if not line:
                break
            i += 1
        lines.insert(i, 'X-Peer: %s' % peer[0])
        data = NEWLINE.join(lines)

        #TODO here is the difference
        # refused = self._deliver(mailfrom, rcpttos, data)
        refused = self._deliver(mailfrom, rcpttos, data.encode('utf-8'))
        # TBD: what to do with refused addresses?
        print('we got some refusals:', refused, file=DEBUGSTREAM)

    def _deliver(self, mailfrom, rcpttos, data):
        import smtplib
        refused = {}
        try:
            s = smtplib.SMTP()
            s.connect(self._remoteaddr[0], self._remoteaddr[1])
            try:
                refused = s.sendmail(mailfrom, rcpttos, data)
            finally:
                s.quit()
        except smtplib.SMTPRecipientsRefused as e:
            print('got SMTPRecipientsRefused', file=DEBUGSTREAM)
            refused = e.recipients
        except (OSError, smtplib.SMTPException) as e:
            print('got', e.__class__, file=DEBUGSTREAM)
            # All recipients were refused.  If the exception had an associated
            # error code, use it.  Otherwise,fake it with a non-triggering
            # exception code.
            errcode = getattr(e, 'smtp_code', -1)
            errmsg = getattr(e, 'smtp_error', 'ignore')
            for r in rcpttos:
                refused[r] = (errcode, errmsg)
        return refused


class ReportSMTPServer(ModifiedPureProxy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_message(self, peer, mailfrom, rcpttos, data, mail_options=None, rcpt_options=None):
        ModifiedPureProxy.process_message(self, peer, mailfrom, rcpttos, 'test')

if __name__ == "__main__":
    # from aiosmtpd.controller import Controller
    # controller = Controller(Proxy(remote_hostname="localhost", remote_port=1025))
    # controller.start()

    server = ReportSMTPServer(("localhost", 1025), ("mail", 25))
    asyncore.loop()