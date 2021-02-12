#!/usr/bin/python
# coding=utf-8
# -*- coding: utf-8 -*-

import re
import os, sys
import requests
import vk_api
import random
from bs4 import BeautifulSoup

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

vk_session = vk_api.VkApi(token='9f480882c352f231188eb392272c579391cd22752abfa7c9d7c063f6efd6a64581e241e552dd99e11e974')
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

sessions = {}

keyboard = VkKeyboard(one_time=False)
keyboard.add_button('👤 Профиль', color=VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button('📗 Последние оценки', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('🏆 Средние оценки', color=VkKeyboardColor.PRIMARY)
keyboard.add_line()
keyboard.add_button('📖 Расписание', color=VkKeyboardColor.PRIMARY)
keyboard.add_line()
keyboard.add_button('📔 Дневник', color=VkKeyboardColor.NEGATIVE)

inlineKeyboard = VkKeyboard(one_time=False, inline=True)
inlineKeyboard.add_button(
        label="Следующая неделя",
        color=VkKeyboardColor.PRIMARY,
        payload={"action": "text", "label":"Следующая неделя"},
    )

def sendMessage(user_id, text, kb = keyboard):
    vk.messages.send(
        random_id=get_random_id(),
        user_id=user_id,
        message=text,
        keyboard=kb.get_keyboard())


def parse(regexp, input, id = -99):
    if id == -99:
        id = 1
        match = re.compile(regexp).search(input)
        print(match.group((id)).encode("utf-8").decode("utf-8"))
        return match.group(id)
    else:
        match = re.compile(regexp).findall(input)
        print(match)
        return match[id]


for event in longpoll.listen():
    try:

        print(event.raw)
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            peer_id = event.peer_id
            cmd = str(event.text).split(" ")
            if cmd[0] == '/login':
                try:
                    sendMessage(peer_id, "Авторизация..")
                    sessions[peer_id] = requests.session()
                    sessions[peer_id].headers = {'Content-Type': 'application/x-www-form-urlencoded'}

                    payload = "username=" + cmd[1] + "&password=" + cmd[2] + "&return_uri=/"
                    auth = sessions[peer_id].post('https://riso.sev.gov.ru/ajaxauthorize', data=payload)

                    if auth.json()['result']:
                        mainPage = sessions[peer_id].get("https://riso.sev.gov.ru" + auth.json()['actions'][0]['url'])
                        username = parse("<div class=\"navigation-top-item__label\">(.*?)</div>", mainPage.content.decode("utf-8"), 2)
                        txt = "✅ Привет, " + username + " Теперь ты можешь полностью использовать рис, не выходя из этой переписки!"
                        sendMessage(peer_id, txt)
                    else:
                        sendMessage(peer_id, "🙅 Неудачная попытка авторизоваться, возможно неправильный пароль!")

                except NameError:
                    print("Error: " + str(sys.exc_info()[0]))
                    sendMessage(peer_id, "Использование: /login [Логин] [Пароль]")
                except IndexError:
                    sendMessage(peer_id, "Использование: /login [Логин] [Пароль]")

            if event.text == 'Начать':
                sendMessage(peer_id, '✍️ Бот для удобной работы с платформой рИСо.\n\n💬 Авторизуйтесь для начала: /login [Логин] [Пароль]\n\n' \
                             + 'Смена пароля возможна тут: https://riso.sev.gov.ru/journal-user-security-action')
            if event.text == '👤 Профиль':
                try:
                    mainPage = sessions[peer_id].get("https://riso.sev.gov.ru")
                    soup = BeautifulSoup(mainPage.content)
                    title = parse("<div class=\"logo__title\">(.*?)</div>",
                                  mainPage.content.decode("utf-8"))
                    city = parse("<div class=\"logo__subtitle\">(.*?)</div>",
                                 mainPage.content.decode("utf-8"))
                    username = parse("<div class=\"navigation-top-item__label\">(.*?)</div>",
                                     mainPage.content.decode("utf-8"),
                                     2)

                    journalPage = sessions[peer_id].get("https://riso.sev.gov.ru/journal-student-monitoring-action")
                    jpage = BeautifulSoup(journalPage.content)
                    midValue = parse(" class=\"green\">(.*?)<span class=\"value-arrow\">",
                                     journalPage.content.decode("utf-8"))
                    mustDo = parse("<div class=\"page-empty page-empty--small\">(.*?)</div>",
                                   journalPage.content.decode("utf-8"))
                    currCategoryTitle = jpage.find("h5").text
                    currCategory = ""
                    try:
                        currCategory = jpage.find("div", "lgray").text
                    except:
                        currCategory = ""

                    schedulePage = sessions[peer_id].get("https://riso.sev.gov.ru/journal-schedule-action")
                    c_group = BeautifulSoup(schedulePage.content)
                    uGroup = c_group.find("h1").text
                    msg = "🏫 Учебное учреждение: " + title + "\n" + \
                          "🌆 Город: " + city + "\n" + "\n" \
                          "👤 Пользователь: " + username + "\n" + \
                          "👥 Группа: " + uGroup + "\n\n" + \
                          "👍 Средний балл: " + midValue + "\n" + \
                          "⛔️ Долги: " + mustDo + "\n" + \
                          "🗒 Текущая категория: " + currCategoryTitle + " - " + currCategory
                    sendMessage(peer_id, msg)
                except KeyError:
                    sendMessage(peer_id, "Сначала нужно авторизоваться: /login [Логин] [Пароль]")

            if event.text == "📔 Дневник":
                try:
                    msg = '📔 Дневник \n\n'
                    mainPage = sessions[peer_id].get("https://riso.sev.gov.ru/journal-app/")

                    soup = BeautifulSoup(mainPage.content)
                    for each_div in soup.findAll('div', {'class': 'dnevnik-day'}):
                        day = "⭐  " + each_div.find("div", "dnevnik-day__title").text.replace("\n", "").replace(
                            "                ", "")
                        lessons = ""
                        for lesson in each_div.findAll('div', {'class': 'dnevnik-lesson'}):
                            id = lesson.find("div", "dnevnik-lesson__number dnevnik-lesson__number--time").text.replace(
                                "\n", "").replace(" ", "")
                            time = lesson.find("div", "dnevnik-lesson__time").text.replace("\n", "").replace(" ", "")
                            lesson.find("div", "dnevnik-lesson__time").decompose()
                            subject = lesson.find("div", "dnevnik-lesson__subject").text.replace("\n", "").replace(
                                "                                    ", ""). \
                                replace("        ", "")
                            marks = lesson.find("div", "dnevnik-lesson__marks").text.replace("\n", "").replace(" ", "")
                            lessons += (id + " " + time + " - " + subject + " - " + marks) + "\n"
                        if lessons == "":
                            lessons = "---\n"
                        msg += day + "\n" + lessons + "\n";

                    sendMessage(peer_id, msg, inlineKeyboard)

                except KeyError:
                    sendMessage(peer_id, "Сначала нужно авторизоваться: /login [Логин] [Пароль]")

            if event.text == "Следующая неделя":
                try:
                    msg = '📔 Дневник \n\n'
                    mainPage = sessions[peer_id].get("https://riso.sev.gov.ru/journal-app/week.-1")

                    soup = BeautifulSoup(mainPage.content)
                    for each_div in soup.findAll('div', {'class': 'dnevnik-day'}):
                        day = "⭐  " + each_div.find("div", "dnevnik-day__title").text.replace("\n", "").replace(
                            "                ", "")
                        lessons = ""
                        for lesson in each_div.findAll('div', {'class': 'dnevnik-lesson'}):
                            id = lesson.find("div", "dnevnik-lesson__number dnevnik-lesson__number--time").text.replace(
                                "\n", "").replace(" ", "")
                            time = lesson.find("div", "dnevnik-lesson__time").text.replace("\n", "").replace(" ", "")
                            lesson.find("div", "dnevnik-lesson__time").decompose()
                            subject = lesson.find("div", "dnevnik-lesson__subject").text.replace("\n", "").replace(
                                "                                    ", ""). \
                                replace("        ", "")
                            marks = lesson.find("div", "dnevnik-lesson__marks").text.replace("\n", "").replace(" ", "")
                            lessons += (id + " " + time + " - " + subject + " - " + marks) + "\n"
                        if lessons == "":
                            lessons = "---\n"
                        msg += day + "\n" + lessons + "\n";

                    sendMessage(peer_id, msg, inlineKeyboard)

                except KeyError:
                    sendMessage(peer_id, "Сначала нужно авторизоваться: /login [Логин] [Пароль]")

            if event.text == '📖 Расписание':
                try:
                    mainPage = sessions[peer_id].get("https://riso.sev.gov.ru/journal-schedule-action/")
                    soup = BeautifulSoup(mainPage.content)
                    msg = '📖 Расписание на текущую неделю: \n\n'
                    for each_div in soup.findAll('div', {'class': 'schedule__day'}):
                        name = each_div.contents[1].find_all('div', class_='column-40')[0].text
                        name = "⭐  " + name.replace("Понедельник", "Понедельник:").replace("Вторник", "Вторник:").\
                                                     replace("Среда", "Среда:").replace("Четверг", "Четверг:").\
                                                     replace("Пятница", "Пятница:").replace("Суббота", "Суббота:").\
                                                     replace("\n", "")
                        lessons = ""
                        i = 1
                        for lesson in each_div.findAll('span', {'class': 'schedule-lesson'}):
                            i += 1
                            if i % 2 == 0:
                                lessons += lesson.text + "\n"

                        if lessons == "":
                            lessons = "---\n"
                        msg += name + "\n" + lessons + "\n"

                    sendMessage(peer_id, msg)
                except KeyError:
                    sendMessage(peer_id, "Сначала нужно авторизоваться: /login [Логин] [Пароль]")

            if event.text == '🏆 Средние оценки':
                try:
                    msg = "🏆 Средние оценки по урокам: \n\n"
                    mainPage = sessions[peer_id].get("https://riso.sev.gov.ru/journal-student-monitoring-action")
                    soup = BeautifulSoup(mainPage.content)
                    for each_div in soup.findAll('table',
                                                 {'class': 'ej-table ej-table--100percent ej-table--colored-lines'}):
                        obj = each_div.contents[3].findAll('tr')
                        for item in obj:
                            mark = item.span.text
                            if mark == "":
                                mark = "N/A"
                            msg += item.td.text + " - " + mark + "\n"

                    sendMessage(peer_id, msg)
                except KeyError:
                    sendMessage(peer_id, "Сначала нужно авторизоваться: /login [Логин] [Пароль]")


            if event.text == '📗 Последние оценки':
                try:
                    mainPage = sessions[peer_id].get("https://riso.sev.gov.ru")
                    txt = "📗 Последние оценки: \n\n"
                    soup = BeautifulSoup(mainPage.content)
                    for each_div in soup.findAll('li', {'class': 'ej-accordion ej-accordion--expanded'}):
                        name = each_div.contents[1].find("div", "ej-accordion__title green").text
                        mark = each_div.contents[3].text.replace(" ", "").replace("\n", "").replace(",", ", ").replace("(",
                                                                                                                       " (")
                        txt += name + " - " + mark + "\n"

                    sendMessage(peer_id, txt)
                except KeyError:
                    sendMessage(peer_id, "Сначала нужно авторизоваться: /login [Логин] [Пароль]")

            if event.text == '/test':
                sendMessage(peer_id, "works")

            if event.text == '/stop':
                sys.exit()
    except NameError:
        print('An exception occurred');