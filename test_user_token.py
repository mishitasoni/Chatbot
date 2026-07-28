import telebot
import sys

token = "8731013547:AAFZaHldnMzjg9_phSiPBDW3GNRpI9bMU2o"
try:
    bot = telebot.TeleBot(token)
    me = bot.get_me()
    print("VALID:", me.username)
except Exception as e:
    print("INVALID:", e)
