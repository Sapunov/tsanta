import requests
import logging

from django.conf import settings


log = logging.getLogger('main.' + __name__)


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
    except requests.exceptions.RequestException as exc:
        log.exception('Exception while request %s: %s', api_url, exc)
        return False

    if ans.status_code == 200:
        json = ans.json()
        if 'id' in json:
            return json['id'].rstrip('>').lstrip('<')

    return False


def get_all_results(utc_begin, utc_end):
    '''Возвращает все события, которые есть у провайдера
        за данный промежуток времени.

        Важно: timestamp от провайдера возвращается по московскому времени
    '''

    api_url = settings.MAILGUN_API_URL +settings.DOMAIN_NAME + "/events"
    params = {
        'begin': utc_begin.timestamp(),
        'end': utc_end.timestamp(),
        'ascending': 'yes',
        'limit': settings.MAILGUN_MAX_EVENTS_LIMIT
    }

    items = []

    while True:
        try:
            res = requests.get(
                api_url,
                auth=("api", settings.MAILGUN_SECRET_KEY),
                params=params)

            if res.status_code != 200:
                log.exception('Bad status_code while request %s; ' \
                    'status_code: %s; text: %s', api_url, res.status_code, res.text)
                break

            data = res.json()

            if data['items']:
                items.extend(data['items'])
                if 'next' in data['paging'] and data['paging']['next']:
                    api_url = data['paging']['next']
            else:
                break
        except requests.exceptions.RequestException as exc:
            log.exception('Exception while request %s: %s', api_url, exc)
            break

    return items[::-1]
