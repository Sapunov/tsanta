import requests

from django.conf import settings


def send_html(mail_from, mail_to, subject, mail_html, reply_to=None, tag=None):

    api_url = settings.MAILGUN_API_URL + settings.DOMAIN_NAME + "/messages"

    if isinstance(mail_from, (list, tuple)):
        mail_from = "{0} <{1}>".format(mail_from[0], mail_from[1])
    else:
        mail_from = "<{0}>".format(mail_from)

    if not isinstance(mail_to, (list, tuple, set)):
        mail_to = [mail_to]

    data = {
        "from": mail_from,
        "to": mail_to,
        "subject": subject,
        "html": mail_html
    }

    if reply_to:
        data["h:Reply-To"] = reply_to

    if tag:
        data["o:tag"] = tag

    try:
        ans = requests.post(
            api_url, auth=("api", settings.MAILGUN_SECRET_KEY), data=data)
    except Exception as e:
        return False

    if ans.status_code == 200:
        json = ans.json()
        if 'id' in json:
            return json['id'].rstrip('>').lstrip('<')

    return False
