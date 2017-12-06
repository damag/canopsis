# -*- coding: utf-8 -*-
# --------------------------------
# Copyright (c) 2015 "Capensis" [http://www.capensis.com]
#
# This file is part of Canopsis.
#
# Canopsis is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Canopsis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Canopsis.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------
from __future__ import unicode_literals

from canopsis.common.ws import route

from bottle import HTTPError
from bottle import request
import requests
import json

from email import Encoders
from email import charset
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate

import smtplib
import socket
import re

SMTP_HOST = 'localhost'
SMTP_PORT = 25
ACCOUNT = 'canopsis@capensis.fr'

def exports(ws):
    @ws.application.post(
        '/api/v2/mail'
    )
    def send_mail():
        try:
            mail_info = request.json
        except ValueError as verror:
            return json.dumps({'result':{'description':'wrong json'},'status':500})
        if mail_info is None:
            return json.dumps({'result':{'description':'None'},'status':500})

        recipients = mail_info.get('recipients', '')
        if isinstance(recipients, str):
            recipients = [recipients]

        res = sendmail(
            mail_info.get('account', ACCOUNT),
            recipients,
            mail_info.get('subject', 'Canopsis alarm report'),
            mail_info.get('body', ''),
            mail_info.get('smtp_host', SMTP_HOST),
            int(mail_info.get('smtp_port', SMTP_PORT))
        )
        return json.dumps({'result':{'description':'{0}'.format(res)},'status':200})

def sendmail(fromaddr, toaddrs, subject, message, smtp_host, smtp_port):
    msg = ("From: {}\r\nTo: {}\r\n\r\nSubject: {}\n\n".format(fromaddr, ", ".join(toaddrs), subject))
    msg = msg + message
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()