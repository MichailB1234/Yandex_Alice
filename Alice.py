import random
import datetime
from flask import Flask, request
import logging
from flask_ngrok import run_with_ngrok
import json
import httplib2
import requests


class HttpApl(object):
    def __init__(self):
        self.SESSION = requests.Session()
        # self.SESSION.headers.update(AUTH_HEADER)

        self.API_VERSION = 'v1'
        self.API_BASE_URL = 'https://dialogs.yandex.net/api/'
        self.API_URL = self.API_BASE_URL + '/' + self.API_VERSION + '/'
        self.skills = ''

    def set_auth_token(self, token):
        self.SESSION.headers.update(self.get_auth_header(token))

    def get_auth_header(self, token):
        return {
            'Authorization': 'OAuth %s' % token
        }

    def log(self, error_text):
        log_file = open('YandexApi.log', 'a')
        log_file.write(error_text + '\n')
        log_file.close()

    def validate_api_response(self, response, required_key_name=None):
        content_type = response.headers['Content-Type']
        content = json.loads(response.text) if 'application/json' in content_type else None
        print(content)
        if response.status_code == 200:
            if required_key_name and required_key_name not in content:
                self.log('Unexpected API response. Missing required key: %s' % required_key_name)
                return None
        elif content and 'error_message' in content:
            self.log('Error API response. Error message: %s' % content['error_message'])
            return None
        elif content and 'message' in content:
            print(1)
            self.log('Error API response. Error message: %s' % content['message'])
            return None
        else:
            response.raise_for_status()

        return content

    ################################################
    # Проверить занятое место                      #
    #                                              #
    # Вернет массив                                #
    # - total - Сколько всего места осталось       #
    # - used - Занятое место                       #
    ################################################
    def checkOutPlace(self):
        result = self.SESSION.get('https://dialogs.yandex.net/api/v1/status')
        content = self.validate_api_response(result)
        if content is not None:
            return content['images']['quota']
        return None

    ################################################
    # Загрузка изображения из интернета            #
    #                                              #
    # Вернет массив                                #
    # - id - Идентификатор изображения             #
    # - origUrl - Адрес изображения.               #
    ################################################
    def downloadImageUrl(self):
        path = 'https://dialogs.yandex.net/api/v1/skills/{skills_id}/images'.format(skills_id=self.skills)
        data1 = json.dumps({"url": ''})
        print(data1)
        result = self.SESSION.post(url=path, data=data1)
        content = self.validate_api_response(result)
        if content is not None:
            return content['image']
        return None

    ################################################
    # Загрузка изображения из файла                #
    #                                              #
    # Вернет массив                                #
    # - id - Идентификатор изображения             #
    # - origUrl - Адрес изображения.               #
    ################################################
    def downloadImageFile(self, url):
        h = httplib2.Http('.cache')
        response, content = h.request(url)
        out = open('img.jpg', 'wb')
        out.write(content)
        out.close()
        path = 'https://dialogs.yandex.net/api/v1/skills/{skills_id}/images'.format(skills_id=self.skills)
        result = self.SESSION.post(url=path, files={'file': ("img.jpg", open("img.jpg", 'rb'))})
        content = self.validate_api_response(result)
        if content is not None:
            return content['image']
        return None

    def downloadImageForEmpty(self):
        path = 'https://dialogs.yandex.net/api/v1/skills/{skills_id}/images'.format(skills_id=self.skills)
        result = self.SESSION.post(url=path, files={'file': ("img2.jpg", open("img2.jpg", 'rb'))})
        content = self.validate_api_response(result)
        if content is not None:
            return content['image']
        return None

    ################################################
    # Просмотр всех загруженных изображений        #
    #                                              #
    # Вернет массив из изображений                 #
    # - id - Идентификатор изображения             #
    # - origUrl - Адрес изображения.	           #
    ################################################
    def getLoadedImages(self):
        path = 'https://dialogs.yandex.net/api/v1/skills/{skills_id}/images'.format(skills_id=self.skills)
        result = self.SESSION.get(url=path)
        content = self.validate_api_response(result)
        if content is not None:
            return content['images']
        return None

    ################################################
    # Удаление выбранной картинки                  #
    #                                              #
    # В случае успеха вернет 'ok'	               #
    ################################################
    def deleteImage(self, img_id):
        path = 'https://dialogs.yandex.net/api/v1/skills/{skills_id}/images/{img_id}'.format(skills_id=self.skills,
                                                                                             img_id=img_id)
        result = self.SESSION.delete(url=path)
        content = self.validate_api_response(result)
        if content is not None:
            return content['result']
        return None

    def deleteAllImage(self):
        success = 0
        fail = 0
        images = self.getLoadedImages()
        for image in images:
            image_id = image['id']
            if image_id:
                if self.deleteImage(image_id):
                    success += 1
                else:
                    fail += 1
            else:
                fail += 1

        return {'success': success, 'fail': fail}


def date_event(date):
    action = "date&filter=" + date
    event_url = f'https://62go.ru/api/get/?key=Nnf8osgw4jslnsl346774fliw&action={action}'
    response = requests.get(event_url)
    data = response.json()
    if data["status"] == "success":
        return data
    else:
        return False


app = Flask(__name__)
run_with_ngrok(app)
logging.basicConfig(level=logging.INFO)
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(request.json, response)
    logging.info(f'Response:  {response!r}')
    return json.dumps(response)


def handle_dialog(req, res):
    user_text = req['request']['original_utterance'].lower()
    http_alice = HttpApl()
    http_alice.set_auth_token(token='AQAAAAAyigh0AAT7owB9e2IY0EWppzGMmGO8t4g')
    http_alice.skills = 'bf9900c2-5f6d-4a72-a8a3-a2321671a44e'
    today = datetime.date.today()
    user_id = req['session']['user_id']
    if req['session']['new']:
        sessionStorage[user_id] = {
            'suggests': [
                "Ближайшее событие",
                "Событие сегодня",
                "Событие завтра",
                "Событие послезавтра",
                "Помощь",
                "Выход",
            ]
        }
        res['response']['text'] = "Здравствуйте, здесь вы сможете узнать интересные события, на которые " \
                                  "вы сможете сходить в Рязани!"
        res['response']['buttons'] = get_suggests(user_id)
        return

    months = [["01", "январь"], ["02", "февраль"], ["03", "март"], ["04", 'апрель'], ["05", 'май'], ["06", 'июнь'],
              ["07", 'июль'], ["08", 'август'], ["09", 'сентябрь'], ["10", 'октябрь'], ["11", 'ноябрь'],
              ["12", 'декабрь'],
              ["01", "января"], ["02", "февраля"], ["03", "марта"], ["04", 'апреля'], ["05", 'мая'], ["06", 'июня'],
              ["07", 'июля'], ["08", 'августа'], ["09", 'сентября'], ["10", 'октября'], ["11", 'ноября'],
              ["12", 'декабря']]
    event_time1 = ["ближайшее", "скорое"]
    event_time2 = ["сегодня", "на сегодняшний", "сегодняшнее"]
    event_time3 = ["завтра", "на завтрашний", "завтрашнее"]
    event_time4 = ["послезавтра", "на послезавтрашний", "послезавтрашнее"]
    flag = True
    for K in range(1):
        if "перейти" in user_text and "источник" in user_text:
            res['response']['text'] = "Отправляю вас в источник."
            res['response']['buttons'] = get_suggests(user_id)
            flag = False
        if "помощь" in user_text:
            res['response']['text'] = 'Чтобы узнать событие напишите день месяц и год события, например: 20 июня 2021  ' \
                                      'или другое обозначение времени события, например: событие на сегодня,' \
                                      ' ближайшее событие.'
            flag = False
            res['response']['buttons'] = get_suggests(user_id)
        if "выход" in user_text:
            res['response']['text'] = 'Завершаю работу. До свидания!'
            res['response']['end_session'] = True
            return
        for i in event_time1:
            if i in user_text:
                action = "first"
                event_url = f'https://62go.ru/api/get/?key=Nnf8osgw4jslnsl346774fliw&action={action}'
                response = requests.get(event_url)
                data = response.json()
                title = data["data"]["NAME"]
                if data["data"]['PICTURE'] is not None:
                    picture_url = "https://62go.ru" + data["data"]['PICTURE']
                    id_picture = http_alice.downloadImageFile(picture_url)["id"]
                    res['response']['card'] = {}
                    res['response']['card']['type'] = 'BigImage'
                    res['response']['card']['title'] = title
                    res['response']['card']['image_id'] = id_picture
                    res['response']['text'] = title
                    res['response']['buttons'] = add_suggest(user_id, data["data"]['DETAIL_PAGE_URL'])
                else:
                    id_picture2 = http_alice.downloadImageForEmpty()["id"]
                    res['response']['card'] = {}
                    res['response']['card']['type'] = 'BigImage'
                    res['response']['card']['title'] = title
                    res['response']['card']['image_id'] = id_picture2
                    res['response']['text'] = title
                    res['response']['buttons'] = add_suggest(user_id, data["data"]['DETAIL_PAGE_URL'])
                flag = False
        for i in event_time2:
            if i in user_text:
                time = today
                mainTime = time.strftime('%d.%m.%Y')
                data = date_event(mainTime)
                if data != False:
                    title = data["data"][0]["NAME"]
                    if data["data"][0]['PICTURE'] is not None:
                        picture_url = "https://62go.ru" + data["data"][0]['PICTURE']
                        id_picture = http_alice.downloadImageFile(picture_url)["id"]
                        res['response']['card'] = {}
                        res['response']['card']['type'] = 'BigImage'
                        res['response']['card']['title'] = title
                        res['response']['card']['image_id'] = id_picture
                        res['response']['text'] = title
                        res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                    else:
                        id_picture2 = http_alice.downloadImageForEmpty()["id"]
                        res['response']['card'] = {}
                        res['response']['card']['type'] = 'BigImage'
                        res['response']['card']['title'] = title
                        res['response']['card']['image_id'] = id_picture2
                        res['response']['text'] = title
                        res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                else:
                    res['response']['text'] = 'Сегодня нет событий.'
                    res['response']['buttons'] = get_suggests(user_id)
                data = False
                flag = False
        for i in event_time3:
            if i in user_text:
                time = today + datetime.timedelta(days=1)
                mainTime = time.strftime('%d.%m.%Y')
                data = date_event(mainTime)
                if data != False:
                    title = data["data"][0]["NAME"]
                    if data["data"][0]['PICTURE'] is not None:
                        picture_url = "https://62go.ru" + data["data"][0]['PICTURE']
                        id_picture = http_alice.downloadImageFile(picture_url)["id"]
                        res['response']['card'] = {}
                        res['response']['card']['type'] = 'BigImage'
                        res['response']['card']['title'] = title
                        res['response']['card']['image_id'] = id_picture
                        res['response']['text'] = title
                        res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                    else:
                        id_picture2 = http_alice.downloadImageForEmpty()["id"]
                        res['response']['card'] = {}
                        res['response']['card']['type'] = 'BigImage'
                        res['response']['card']['title'] = title
                        res['response']['card']['image_id'] = id_picture2
                        res['response']['text'] = title
                        res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                else:
                    res['response']['text'] = 'Завтра нет событий.'
                    res['response']['buttons'] = get_suggests(user_id)
                flag = False
        for i in event_time4:
            if i in user_text:
                time = today + datetime.timedelta(days=2)
                mainTime = time.strftime('%d.%m.%Y')
                data = date_event(mainTime)
                if data != False:
                    title = data["data"][0]["NAME"]
                    if data["data"][0]['PICTURE'] is not None:
                        picture_url = "https://62go.ru" + data["data"][0]['PICTURE']
                        id_picture = http_alice.downloadImageFile(picture_url)["id"]
                        res['response']['card'] = {}
                        res['response']['card']['type'] = 'BigImage'
                        res['response']['card']['title'] = title
                        res['response']['card']['image_id'] = id_picture
                        res['response']['text'] = title
                        res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                    else:
                        id_picture = http_alice.downloadImageForEmpty()["id"]
                        res['response']['card'] = {}
                        res['response']['card']['type'] = 'BigImage'
                        res['response']['card']['title'] = title
                        res['response']['card']['image_id'] = id_picture
                        res['response']['text'] = title
                        res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                else:
                    res['response']['text'] = 'Послезавтра нет событий.'
                    res['response']['buttons'] = get_suggests(user_id)
                flag = False
        for i in months:
            if i[1] in user_text:
                month = i[0]
                text = (req['request']['original_utterance'].lower()).split()
                year1 = False
                day1 = False
                for j in text:
                    if j.isdigit():
                        if len(j) == 4:
                            year1 = True
                            year = j
                        elif len(j) > 2:
                            continue
                        elif int(j) <= 31:
                            day1 = True
                            day = j
                    if year1 is True and day1 is True:
                        mainTime = f'{day}.{month}.{year}'
                        data = date_event(mainTime)
                        if data != False:
                            title = data["data"][0]["NAME"]
                            if data["data"][0]['PICTURE'] is not None:
                                picture_url = "https://62go.ru" + data["data"][0]['PICTURE']
                                print(picture_url)
                                id_picture = http_alice.downloadImageFile(picture_url)["id"]
                                title = data["data"][0]["NAME"]
                                res['response']['card'] = {}
                                res['response']['card']['type'] = 'BigImage'
                                res['response']['card']['title'] = title
                                res['response']['card']['image_id'] = id_picture
                                res['response']['text'] = title
                                res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                            else:
                                id_picture = http_alice.downloadImageForEmpty()["id"]
                                res['response']['card'] = {}
                                res['response']['card']['type'] = 'BigImage'
                                res['response']['card']['title'] = title
                                res['response']['card']['image_id'] = id_picture
                                res['response']['text'] = title
                                res['response']['buttons'] = add_suggest(user_id, data["data"][0]['DETAIL_PAGE_URL'])
                        else:
                            res['response']['text'] = f'{day}.{month}.{year} нет событий.'
                            res['response']['buttons'] = get_suggests(user_id)
                        flag = False
                        break
                else:
                    res['response']['text'] = 'Вы не указали число месяца или год.'
                    res['response']['buttons'] = get_suggests(user_id)
        if flag is False:
            break
    else:
        other = ["Я не понимаю.", "Не могу разобрать.", "Пожалуйста, напишите разборчивее."]
        res['response']['text'] = random.choice(other)
        res['response']['buttons'] = get_suggests(user_id)


def get_suggests(user_id):
    session = sessionStorage[user_id]

    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:6]
    ]
    sessionStorage[user_id] = session

    return suggests

def add_suggest(user_id, url):
    session = sessionStorage[user_id]

    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests']
    ]
    sessionStorage[user_id] = session
    suggest1 = [{
        "title": "Перейти в источник",
        "url": url,
        "hide": True
    }]
    suggests = suggest1 + suggests
    return suggests

if __name__ == '__main__':
    app.run()
