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
        res = sendmail(
            mail_info.get('account', 'root'),
            mail_info.get('recipients', ''),
            mail_info.get('subject', 'mail from canopsis'),
            mail_info.get('body', ''),
            mail_info.get('attachments', None),
            mail_info.get('smtp_host', 'localhost'),
            mail_info.get('smtp_port', 25),
            mail_info.get('html', False)
       )
        return json.dumps({'result':{'description':'{0}'.format(res) },'status':200})

def sendmail(
        account_mail, recipients, subject, body, attachments, smtp_host,
        smtp_port, html
):
    """
    :param account: Account or nothing for anon.
    :param recipients: str("glehee@capensis.fr"), Account list of (Account
        or string).
    :param subject: str("My Subject").
    :param body: str("My Body").
    :param attachments: File, list of File.
    :param smtp_host: str("localhost").
    :param smtp_port: int(25).
    :param html: allow html into mail body (booleen).
    """

    charset.add_charset('utf-8', charset.SHORTEST, charset.QP)

    if not re.match(
            "^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.([a-zA-Z]{2,6})?$",
            str(account_mail)
    ):
        return (
            2,
            'Invalid Email format for sender: {0}'.format(account_mail)
        )

    # Verify recipients
    if not recipients:
        return (2, 'No recipients configured')

    if not isinstance(recipients, list):
        recipients = [recipients]

    dests = []

    for dest in recipients:
        if isinstance(dest, basestring):
            if re.match(
                    "^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.([a-zA-Z]{2,6})?$",
                    dest
            ):
                dest_mail = dest
        else:
            self.logger.error(
                'Ignoring invalid recipient: {0}'.format(dest))

    dests_str = ', '.join(dests)

    # Verify attachments
    if attachments:
        storage = Storage(account=account, namespace='object')

        if not isinstance(attachments, list):
            attachments = [attachments]

    # Send

    msg = MIMEMultipart()
    msg["From"] = account_mail
    msg["To"] = dests_str
    msg["Subject"] = subject

    if html:
        msg.attach(MIMEText(body, 'html', _charset='utf-8'))

    else:
        msg.attach(MIMEText(body, 'plain', _charset='utf-8'))

    msg['Date'] = formatdate(localtime=True)

    if attachments:
        for _file in attachments:
            part = MIMEBase('application', "octet-stream")

            if not isinstance(_file, File):
                _file.__class__ = File

            #meta_file = _file.get(storage)
            content_file = _file.get(storage)
            part.set_payload(content_file)
            Encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                'attachment; filename="%s"' % _file.data['file_name'])
            part.add_header('Content-Type', _file.data['content_type'])
            msg.attach(part)

    sock = socket.socket()

    try:
        sock.connect((smtp_host, smtp_port))

    except Exception as err:
        return (
            2,
            'Connection to SMTP <{0}:{1}> failed: {2}'.format(
                smtp_host, smtp_port, err
            )
        )

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        verif = server.verify()
        server.sendmail(account_mail, dests, msg.as_string())
        server.quit()

    except Exception as err:
        return (
            2,
            "Impossible to send mail: {0} server verify {1}".format(err, verif)
        )

    return (0, "Mail sent successfully")

