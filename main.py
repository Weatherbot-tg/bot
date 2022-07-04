import config,text
from db import BotDB

from datetime import datetime,timedelta,date
import aioschedule
import asyncio
import os
import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from pyowm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import NotFoundError

logging.basicConfig(level=logging.INFO)

config_dict = get_default_config()
config_dict['language'] = config.OWM_LANGUAGE

BotDB = BotDB(config.DB_NAME,config.DB_USER,config.DB_PASSWORD,config.DB_HOST,config.DB_PORT)
bot = Bot(config.BOT_TOKEN)
owm = OWM(config.OWM_TOKEN, config_dict)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

mgr = owm.weather_manager()
geo_mgr = owm.geocoding_manager()
uv_mgr = owm.uvindex_manager()
air_mgr = owm.airpollution_manager()

class Form(StatesGroup):
    weather_place = State()
    weather_zip = State() 
    weather_coordinates = State()
    air_pollution = State()
    get_geo = State()
    report = State()
    uv_index = State()
    db_place = State()

def is_subscribed(chat_member):
    if chat_member['status'] != 'left':
        return True
    else:
        return False

async def send_subscribe(message: types.Message):
    buttons = types.InlineKeyboardMarkup()
    btn_sub_1 = types.InlineKeyboardButton(text=text.btn_sub_1_text, url=config.SUBSCRIBE_LINK)
    btn_sub_2 = types.InlineKeyboardButton(text=text.btn_sub_2_text, url=config.SUBSCRIBE_LINK)
    buttons.add(btn_sub_1,btn_sub_2)
    if not is_subscribed(await bot.get_chat_member(chat_id=config.CHANNEL_ID,user_id = message.from_user.id)):
        await bot.send_message(message.chat.id,text.subscribe_text,reply_markup = buttons)

def check_exist(place):
    try:
        observation = mgr.weather_at_place(place)
        return True
    
    except:
        return False

def handle_weather(place,weather_type):
    try:
        if int(weather_type) == 1:
            observation = mgr.weather_at_place(place)
            weather = observation.weather

        elif int(weather_type) == 2:
            place = place.split(',')
            weather = mgr.weather_at_coords(float(place[0]), float(place[1])).weather 
            list_of_locations = geo_mgr.reverse_geocode(float(place[0]), float(place[1]))
            place = list_of_locations[0].name

        elif int(weather_type) == 3:
            place = place.split(',')
            weather = mgr.weather_at_zip_code(str(place[0]),str(place[1])).weather
            place = f'{place[0]} , {place[1]}'
        
        temp_manager = weather.temperature("celsius")
        wind = weather.wind()
        recomendations = list()
        recomendation = ''
        rain_value = ''

        if weather.status == "Shower rain" or weather.status == "Rain": recomendations.append(text.recomendations[0])
        if weather.status == "Thunderstorm":recomendations.append(text.recomendations[1])
        if int(weather.visibility_distance) < 3500: recomendations.append(text.recomendations[2])
        if int(wind['speed']) > 9:recomendations.append(text.recomendations[3])
        if int(temp_manager['temp']) > 25 and weather.status != "Shower rain" and weather.status != "Rain" and weather.status != "Thunderstorm" and int(wind['speed'] < 5):recomendations.append(text.recomendations[4])
        if int(temp_manager['temp']) > 15 and weather.status != "Shower rain" and weather.status != "Rain" and weather.status != "Thunderstorm": recomendations.append(text.recomendations[5])
        if int(temp_manager['temp']) < 14: recomendations.append(text.recomendations[6])
        if int(temp_manager['temp']) < 0: recomendations.append(text.recomendations[7])
        if int(temp_manager['temp']) < -10: recomendations.append(text.recomendations[8])
        if int(weather.humidity) > 80 and weather.status != "Shower rain" and weather.status != "Rain" and weather.status != "Thunderstorm": recomendations.append(text.recomendations[9])

        if recomendations:
            recomendation = ',\n'.join(map(str,recomendations))
            recomendation = f"{text.recomendation_text}{recomendation} \n\n"

        else:recomendation = ''

        if weather.status == "Shower rain" or weather.status == "Rain":
            try:
                r = weather.rain
                rain_value = f'{text.rain_1} {r["1h"]} {text.rain_2} \n\n'
            except:pass

        return( f"= {text.weather_parameters[8]} {text.first_line_types[int(weather_type)]} {place} =\n"+
        		f"┌ {text.weather_parameters[0]} {temp_manager['temp_min']} - {temp_manager['temp_max']} °C  ({temp_manager['temp']} °C)\n" +
				f"├ {text.weather_parameters[1]} {temp_manager['feels_like']} °C\n" +
				f"├ {text.weather_parameters[2]} {wind['speed']} м/с\n" +
                f"├ {text.weather_parameters[3]} {wind['deg']} °\n" +
				f"├ {text.weather_parameters[4]} {round(weather.pressure['press']/133,2)} мм.рт.ст\n" +
				f"├ {text.weather_parameters[5]} {weather.humidity} %\n" +
				f"├ {text.weather_parameters[6]} {weather.visibility_distance/1000} км\n" +
				f"├ {text.weather_parameters[7]} {weather.clouds} %\n" +
				f"└ {weather.detailed_status[0].capitalize() + weather.detailed_status[1:]} {text.icons[weather.weather_icon_name[:-1]]}\n\n"+
                str(recomendation) +
                str(rain_value)+
				f"{text.last_receive_data_text} {weather.reference_time('iso')}")

    except NotFoundError:
        return (f'{text.not_found_types[weather_type]} "{place}" {text.notfound_text}')

    except TimeoutError:
        return text.timeouterror_text

    except Exception as e:
        #await bot.send_message(config.ADMIN_ID,f'[Exception] : ({e})')
        return text.exception_text

@dp.message_handler(commands='start')
async def welcome(message: types.Message):
    BotDB.add_user(message.from_user.id,date.today())
    photo = open(os.path.dirname(os.path.realpath(__file__)) + config.BANNER_PATH, 'rb')
    await bot.send_photo(message.chat.id,photo, text.welcome_text_1 + str(message.from_user.first_name) + text.welcome_text_2)
    await help(message)
    await send_subscribe(message)

@dp.message_handler(commands='donate')
async def get_donate(message:types.Message):
    donate_buttons = types.InlineKeyboardMarkup()
    btn_donate = types.InlineKeyboardButton(text=text.btn_donate_text, url=config.DONATE_LINK)
    donate_buttons.add(btn_donate)
    await bot.send_message(message.chat.id,text.donate_text,reply_markup = donate_buttons)

@dp.message_handler(commands='debug')
async def debug(message: types.Message):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    await message.reply(f"Telegram:\n{message}\n\nServer:\nCurrent time:{current_time}")

@dp.message_handler(commands='help')
async def help(message: types.Message):
	await bot.send_message(message.chat.id, text.help_text)

@dp.message_handler(commands='credits')
async def credits(message: types.Message):
	await bot.send_message(message.chat.id, text.credits_text)

#report
@dp.message_handler(commands='report')
async def get_report(message: types.Message):
    await Form.report.set()
    await bot.send_message(message.chat.id,text.get_report_text)

@dp.message_handler(state=Form.report)
async def send_report(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text
        await bot.send_message(config.ADMIN_ID, f"New report:\nName: {message.from_user.first_name} {message.from_user.last_name}\nUsername: @{message.chat.username}\nMessage: {message.text}\nLanguage: {message.from_user.language_code}\nUser Id: {message.from_user.id}\nChat id {message.chat.id}")
        await bot.send_message(message.chat.id,text.send_report_text_success)

    except:
        await bot.send_message(message.chat.id,text.send_report_text_unsuccess)
    await state.finish()

#air
@dp.message_handler(commands='air_pollution')
async def send_air(message: types.Message):
    await Form.air_pollution.set()
    await bot.send_message(message.chat.id,text.get_coordinates_text)

@dp.message_handler(state=Form.air_pollution)
async def send_air(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text
        msg = message.text
        msg = msg.split(',')
        air_status = air_mgr.air_quality_at_coords(float(msg[0]), float(msg[1]))

        await message.reply(f"┌ CO: {air_status.co}\n"+
                            f"├ NO: {air_status.no}\n"+
                            f"├ NO2: {air_status.no2}\n"+
                            f"├ O3: {air_status.o3}\n"+
                            f"├ SO2: {air_status.so2}\n"+
                            f"├ PM2_5: {air_status.pm2_5}\n"+
                            f"├ PM10: {air_status.pm10}\n"+
                            f"├ NH3: {air_status.nh3}\n"+
                            f"└ {text.send_air_text} {air_status.aqi}\n\n"
                            f"{text.last_receive_data_text} {air_status.reference_time('iso')}")

        await send_subscribe(message)
    except:await message.reply(text.incorrect_data_text)
    await state.finish()

#uv
@dp.message_handler(commands='uv_index')
async def send_uv(message: types.Message):
    await Form.uv_index.set()
    await bot.send_message(message.chat.id,text.get_coordinates_text)

@dp.message_handler(state=Form.uv_index)
async def send_uv(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text
        msg = message.text
        msg = msg.split(',')
        uvi = uv_mgr.uvindex_around_coords(float(msg[0]), float(msg[1]))
        ref_time = uvi.reference_time('iso')
        await message.reply(f'{text.send_uv_text_1}{uvi.value}{text.send_uv_text_1}{ref_time}')
        await send_subscribe(message)
    except: await message.reply(text.incorrect_data_text)
    await state.finish()

#geo
@dp.message_handler(commands='get_geo')
async def get_geo(message: types.Message):
    await Form.get_geo.set()
    await bot.send_message(message.chat.id, text.get_geo_text)

@dp.message_handler(state=Form.get_geo)
async def send_to_geo(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text
        msg = message.text
        msg = msg.split(',')
        list_of_locations = geo_mgr.geocode(msg[0], country=msg[1], limit=1)
        await message.reply(f"{text.send_to_geo_text_1}{list_of_locations[0].lat}, {text.send_to_geo_text_2}{list_of_locations[0].lat}")
        await send_subscribe(message)
    except: await message.reply(text.incorrect_data_text)
    await state.finish()

#name
@dp.message_handler(commands='weather')
async def get_weather(message: types.Message):
    await Form.weather_place.set()
    await bot.send_message(message.chat.id, text.get_weather_text)

@dp.message_handler(state=Form.weather_place)
async def weather_place(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply(handle_weather(message.text,1))
    await send_subscribe(message)
    await state.finish()

#gps
@dp.message_handler(commands='weather_coords')
async def get_coordinates(message: types.Message):
    await Form.weather_coordinates.set()
    await bot.send_message(message.chat.id, text.get_coordinates_text)

@dp.message_handler(state=Form.weather_coordinates)
async def weather_place(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply(handle_weather(message.text,2))
    await send_subscribe(message)
    await state.finish()

#zip
@dp.message_handler(commands='weather_zip')
async def get_coordinates(message: types.Message):
    await Form.weather_zip.set()
    await bot.send_message(message.chat.id, text.get_zip_text)

@dp.message_handler(state=Form.weather_zip)
async def weather_place(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply(handle_weather(message.text,3))
    await send_subscribe(message)
    await state.finish()

@dp.message_handler(commands='subscribe')
async def get_subscribe(message: types.Message):
    subscribe_buttons = types.InlineKeyboardMarkup()
    btn_subscribe = types.InlineKeyboardButton(text=text.subscribe_btn_text, callback_data='subscribe_weather')
    btn_unsubscribe = types.InlineKeyboardButton(text=text.unsubscribe_btn_text, callback_data='unsubscribe_weather')
    btn_edit = types.InlineKeyboardButton(text=text.edit_btn_text, callback_data='edit_weather')
    if (BotDB.user_exists(message.from_user.id) == True):
        subscribe_buttons.add(btn_unsubscribe,btn_edit)
        await bot.send_message(message.chat.id,f'{text.subscribed_text_1}{BotDB.get_record(message.from_user.id)[0][0]}{text.subscribed_text_2}',reply_markup = subscribe_buttons)
    else:
        subscribe_buttons.add(btn_subscribe)
        await bot.send_message(message.chat.id,text.subscribing_text,reply_markup = subscribe_buttons)

@dp.callback_query_handler(text="unsubscribe_weather")
async def unsubscribe_weather(call: types.CallbackQuery):
    BotDB.detete_record(call.from_user.id)
    await bot.send_message(call.from_user.id,text.canceled_subscribe)
    
@dp.callback_query_handler(text=["subscribe_weather","edit_weather"])
async def subscribe_weather(call: types.CallbackQuery):
    await Form.db_place.set()
    await call.message.answer(text.get_weather_text)

@dp.message_handler(state=Form.db_place)
async def send_air(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text

        if check_exist(message.text) == True:
            BotDB.add_record(message.from_user.id,message.text)
            await bot.send_message(message.chat.id,text.record_created_successfully)

        else:
            await bot.send_message(message.chat.id,text.no_such_city)

    except Exception as e:
        await bot.send_message(message.chat.id,text.incorrect_operation)
        print(e)

    await state.finish()

@dp.message_handler(content_types=['text'])
async def send_error(message: types.Message):
    await message.reply(f'{text.notfound_command_text_1}"{message.text}"{text.notfound_command_text_2}')

#Рассылка сообщений
async def send_weather_schedule():
    db = BotDB.get_records()
    for i in db:
        await bot.send_message(i[0],text.schedule_text)
        await bot.send_message(i[0],handle_weather(i[1],1))

async def scheduler():
    aioschedule.every().day.at(config.SCHEDULE_TIME).do(send_weather_schedule)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True,on_startup=on_startup)