import config,text,markups
from db import BotDB
from owm_manager import OwmMGR

from datetime import datetime,timedelta,date
import aioschedule
import asyncio
import os
import logging

import aiogram.utils.markdown as md
from aiogram import __main__ as aiogram_core
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

schedule_logger = logging.getLogger('schedule')
schedule_logger.setLevel(level=logging.DEBUG)

BotDB = BotDB(config.DB_NAME,config.DB_USER,config.DB_PASSWORD,config.DB_HOST,config.DB_PORT)
OwmMGR = OwmMGR(config.OWM_TOKEN,config.OWM_LANGUAGE)

bot = Bot(config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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
    if not is_subscribed(await bot.get_chat_member(chat_id=config.CHANNEL_ID,user_id = message.from_user.id)):
        await bot.send_message(message.chat.id,text.subscribe_text,reply_markup = markups.buttons)

@dp.message_handler(commands='start')
async def welcome(message: types.Message):
    BotDB.add_user(message.from_user.id,date.today())
    photo = open(os.path.dirname(os.path.realpath(__file__)) + config.BANNER_PATH, 'rb')
    await bot.send_photo(message.chat.id,photo, text.welcome_text_1 + str(message.from_user.first_name) + text.welcome_text_2)
    await help(message)
    await send_subscribe(message)

@dp.message_handler(commands='donate')
async def get_donate(message:types.Message):
    await bot.send_message(message.chat.id,text.donate_text,reply_markup = markups.donate_buttons)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(commands='debug')
async def debug(message: types.Message):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    await message.reply(f"Telegram:\n{message}\n\nServer:\n{aiogram_core.SysInfo()}\n\nCurrent time:{current_time}")

@dp.message_handler(commands='help')
async def help(message: types.Message):
    await bot.send_message(message.chat.id, text.help_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(commands='credits')
async def credits(message: types.Message):
    await bot.send_message(message.chat.id, text.credits_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

#report
@dp.message_handler(commands='report')
async def get_report(message: types.Message):
    await Form.report.set()
    await bot.send_message(message.chat.id,text.get_report_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

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
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(state=Form.air_pollution)
async def send_air(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text
            message.text = message.text.split(",")
        await message.reply(OwmMGR.handle_air(message.text[0],message.text[1]))
        await send_subscribe(message)
    except:await message.reply(text.incorrect_data_text)
    await state.finish()

#uv
@dp.message_handler(commands='uv_index')
async def send_uv(message: types.Message):
    await Form.uv_index.set()
    await bot.send_message(message.chat.id,text.get_coordinates_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(state=Form.uv_index)
async def send_uv(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text
            message.text = message.text.split(",")
        await message.reply(OwmMGR.handle_uv(float(message.text[0]),float(message.text[1])))
        await send_subscribe(message)
    except: await message.reply(text.incorrect_data_text)
    await state.finish()

#geo
@dp.message_handler(commands='get_geo')
async def get_geo(message: types.Message):
    await Form.get_geo.set()
    await bot.send_message(message.chat.id, text.get_geo_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(state=Form.get_geo)
async def send_to_geo(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text
        message.text = message.text.split(",")
        await message.reply(OwmMGR.handle_geo(message.text[0],message.text[1]))
        await send_subscribe(message)
    except: await message.reply(text.incorrect_data_text)
    await state.finish()

#name
@dp.message_handler(commands='weather')
async def get_weather(message: types.Message):
    await Form.weather_place.set()
    await bot.send_message(message.chat.id, text.get_weather_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(state=Form.weather_place)
async def weather_place(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.reply(OwmMGR.handle_weather(message.text,1))
    await send_subscribe(message)
    await state.finish()

#gps
@dp.message_handler(commands='weather_coords')
async def get_coordinates(message: types.Message):
    await Form.weather_coordinates.set()
    await bot.send_message(message.chat.id, text.get_coordinates_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(state=Form.weather_coordinates)
async def weather_place(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.reply(OwmMGR.handle_weather(message.text,2))
    await send_subscribe(message)
    await state.finish()

#zip
@dp.message_handler(commands='weather_zip')
async def get_coordinates(message: types.Message):
    await Form.weather_zip.set()
    await bot.send_message(message.chat.id, text.get_zip_text)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.message_handler(state=Form.weather_zip)
async def weather_place(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply(OwmMGR.handle_weather(message.text,3))
    await send_subscribe(message)
    await state.finish()

@dp.message_handler(commands='subscribe')
async def get_subscribe(message: types.Message):
    if (BotDB.user_exists(message.from_user.id) == True):
        await bot.send_message(message.chat.id,f'{text.subscribed_text_1}{BotDB.get_record(message.from_user.id)[0][0]}{text.subscribed_text_2}',reply_markup = markups.subscribed_buttons)
    else:
        await bot.send_message(message.chat.id,text.subscribing_text,reply_markup = markups.subscribe_button)
    BotDB.update_lastvisit(message.from_user.id,date.today())

@dp.callback_query_handler(text="unsubscribe_weather")
async def unsubscribe_weather(call: types.CallbackQuery):
    BotDB.detete_record(call.from_user.id)
    await bot.send_message(call.from_user.id,text.canceled_subscribe)
    BotDB.update_lastvisit(call.from_user.id,date.today())
    
@dp.callback_query_handler(text=["subscribe_weather","edit_weather"])
async def subscribe_weather(call: types.CallbackQuery):
    await Form.db_place.set()
    await call.message.answer(text.get_weather_text)
    BotDB.update_lastvisit(call.from_user.id,date.today())

@dp.message_handler(state=Form.db_place)
async def send_air(message: types.Message,state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text

        if OwmMGR.check_exist(message.text) == True:
            BotDB.add_record(message.from_user.id,message.text,date.today())
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
        await bot.send_message(i[0],OwmMGR.handle_weather(i[1],1),reply_markup = markups.subscribed_buttons)
    await bot.send_message(config.ADMIN_ID,f"{text.success_schedule} {config.SCHEDULE_TIME}+00")

async def scheduler():
    aioschedule.every().day.at(config.SCHEDULE_TIME).do(send_weather_schedule)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())
    print(aiogram_core.SysInfo())
    print(asyncio.get_event_loop())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True,on_startup=on_startup)