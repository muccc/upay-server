#!/usr/bin/env python

import os
import os.path

from upay.server import app
from upay.server.token_authority import TokenAuthority

app.config.from_pyfile(os.path.join(os.getcwd(), 'devserver.cfg'))

if 'USE_SSL' in app.config and app.config['USE_SSL']:
    from OpenSSL import SSL
    context = SSL.Context(SSL.TLSv1_2_METHOD)
    context.use_privatekey_file('test.key')
    context.use_certificate_file('test.crt')

authority = TokenAuthority(app.config)

app.run()
