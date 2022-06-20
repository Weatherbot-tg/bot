import telebot
from telebot import types
from pyowm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import NotFoundError
import config
from datetime import datetime
import os
from loguru import logger

bot = telebot.TeleBot(config.BOT_TOKEN)
icons = {'01':'☀️','02':'🌤','03':'⛅️','04':'☁️','09':'🌧','10':'🌦','11':'⛈','13':'❄️','50':'🌫️'}

config_dict = get_default_config()
config_dict['language'] = 'ru'

owm = OWM(config.OWM_TOKEN, config_dict)

mgr = owm.weather_manager()
geo_mgr = owm.geocoding_manager()
uv_mgr = owm.uvindex_manager()
air_mgr = owm.airpollution_manager()

def is_subscribed(user_id):
    result = bot.get_chat_member(config.CHANNEL_ID, user_id)
    if result.status != 'left':
        return True
    else:
        return False

def send_subscribe(message):
    buttons = types.InlineKeyboardMarkup()
    btn_sub_1 = types.InlineKeyboardButton(text='✔️ Подписаться', url='t.me/+PCNE7tmpVNI1NmEy')
    btn_sub_2 = types.InlineKeyboardButton(text='❌ Скрыть', url='t.me/+PCNE7tmpVNI1NmEy')
    buttons.add(btn_sub_1,btn_sub_2)
    if not is_subscribed(message.chat.id):
        bot.send_message(message.chat.id,"⚠️ Подпишись на наш канал, там мы публикуем новости этого бота! Благодаря этому бот бесплатный",reply_markup = buttons)

@bot.message_handler(commands=['start'])
def welcome(message):
    photo = open(f'{os.path.dirname(os.path.realpath(__file__))}/media/logo-test.png', 'rb')
    bot.send_photo(message.chat.id,photo, '👋 Привет, ' + str(message.from_user.first_name) + '! Меня зовут Weather bot, и я помогу тебе узнавать погоду в любой точке Земли 🌎 в любое время.')
    help(message)
    send_subscribe(message)

@bot.message_handler(commands=['help'])
def help(message):
	bot.send_message(message.chat.id, 'Ты можешь управлять мной, отправляя эти команды:\n\n/help - команды бота\n/credits - автор бота\n/weather - вывод погоды в указанном городе\n/weather_coords - вывод погоды по географическим координатам\n/weather_zip - вывод погоды по почтовому индексу\n/air_pollution - вывод качества воздуха\n/get_geo - получить координаты города\n/uv_index - получить уф индекс\n/report - сообщить об ошибке')

@bot.message_handler(commands=['credits'])
def credits(message):
	bot.send_message(message.chat.id, 'Weather bot by Dmitry Karpenko (@dimkarpenko), Russia\nGitHub - https://github.com/Dimkarpenko/Weatherbot\n\nДанные о погоде взяты с сайта http://openweathermap.org')

@bot.message_handler(commands=['weather'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Введи название города / населённого пункта')
  bot.register_next_step_handler(sent, send_weather,1)

@bot.message_handler(commands=['weather_coords'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Введи координаты (широта,долгота)')
  bot.register_next_step_handler(sent, send_weather,2)

@bot.message_handler(commands=['weather_zip'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Отправь индекс и код страны (101000,Ru)')
  bot.register_next_step_handler(sent, send_weather,3)

@bot.message_handler(commands=['weather_id'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Отправь ID города / населённого пункта')
  bot.register_next_step_handler(sent, send_weather,4)

@bot.message_handler(commands=['id'])
def send_msg(message):
    bot.send_message(message.chat.id, f"Your id is {message.chat.id}")
    a = message.chat.id
    bot.send_message(config.ADMIN_ID, f'{message.chat.username} - {a}')

@bot.message_handler(commands=['report'])
def send_report(message):
    sent = bot.send_message(message.chat.id, 'Отправь твоё сообщение об ошибке')
    bot.register_next_step_handler(sent, send_report)

@bot.message_handler(commands=['air_pollution'])
def send_air(message):
    sent = bot.send_message(message.chat.id, 'Отправь координаты (широта,долгота)')
    bot.register_next_step_handler(sent, send_air)

@bot.message_handler(commands=['uv_index'])
def send_uv(message):
    sent = bot.send_message(message.chat.id, 'Отправь координаты (широта,долгота)')
    bot.register_next_step_handler(sent, send_uv)
  
def send_uv(message):
    msg = message.text
    msg = msg.split(',')
    uvi = uv_mgr.uvindex_around_coords(float(msg[0]), float(msg[1]))
    ref_time = uvi.reference_time('iso')
    bot.reply_to(message,f'УФ - индекс в данной области - {uvi.value}\nВремя последнего сбора данных - {ref_time}')
    send_subscribe(message)

@bot.message_handler(commands=['get_geo'])
def send_to_geo(message):
    sent = bot.send_message(message.chat.id, 'Отправь название города и код страны (Москва,Ru)')
    bot.register_next_step_handler(sent, send_to_geo)

def send_to_geo(message):
    msg = message.text
    msg = msg.split(',')
    list_of_locations = geo_mgr.geocode(msg[0], country=msg[1], limit=1)
    lat = list_of_locations[0].lat
    lon = list_of_locations[0].lon
    bot.reply_to(message,f"Широта - {lat}, Долгота - {lon}")
    send_subscribe(message)

def send_air(message):
    msg = message.text
    msg = msg.split(',')
    lat = float(msg[0])
    lon = float(msg[1])
    air_status = air_mgr.air_quality_at_coords(lat, lon)

    bot.reply_to(message,
        f"┌ CO: {air_status.co}\n"+
        f"├ NO: {air_status.no}\n"+
        f"├ NO2: {air_status.no2}\n"+
        f"├ O3: {air_status.o3}\n"+
        f"├ SO2: {air_status.so2}\n"+
        f"├ PM2_5: {air_status.pm2_5}\n"+
        f"├ PM10: {air_status.pm10}\n"+
        f"├ NH3: {air_status.nh3}\n"+
        f"└ Индекс качества воздуха: {air_status.aqi}\n\n"
        f"Время сбора данных 🕑 {air_status.reference_time('iso')}")

    send_subscribe(message)

def send_report(message):
    try:
        bot.send_message(config.ADMIN_ID, f"New report:\nName: {message.from_user.first_name} {message.from_user.last_name}\nUsername: @{message.chat.username}\nMessage: {message.text}\nDate: {datetime.utcfromtimestamp(int(message.date)).strftime('%Y-%m-%d %H:%M:%S')}\nLanguage: {message.from_user.language_code}\nId: {message.chat.id}")
        bot.send_message(message.chat.id,"Твоё сообщение получено, спасибо!")
    except:
        bot.send_message(message.chat.id,"Не удалось отправить сообщение, попробуй связаться с поддержкой --> @dimkarpenko")
    
def send_weather(message,weather_type):
    try:
        if int(weather_type) == 1:
            place = message.text
            observation = mgr.weather_at_place(place)
            w = observation.weather

        elif int(weather_type) == 2:
            msg = message.text
            msg = msg.split(',')
            lat = float(msg[0])
            lon = float(msg[1])
            w = mgr.weather_at_coords(lat, lon).weather 
            list_of_locations = geo_mgr.reverse_geocode(lat, lon)
            place = list_of_locations[0].name

        elif int(weather_type) == 3:
            msg = message.text
            msg = msg.split(',')
            zip_code = msg[0]
            country = msg[1]
            w = mgr.weather_at_zip_code(str(zip_code),str(country)).weather
            place = f'{zip_code} , {country}'

        elif int(weather_type) == 4:
            msg = int(message.text)
            w = mgr.weather_at_id(msg).weather 
            place = msg

        recomendations = list()

        t = w.temperature("celsius")
        t1 = t['temp']
        t2 = t['feels_like']
        t3 = t['temp_max']
        t4 = t['temp_min']

        wi = w.wind()
        humi = w.humidity
        cl = w.clouds
        st = w.status
        dt = w.detailed_status
        ti = w.reference_time('iso')
        pr = w.pressure['press']
        vd = w.visibility_distance
        icon = w.weather_icon_name[:-1]

        recomendation = ''
        rain_value = ''

        #Подбираем рекомендации по погоде
        if st == "Shower rain" or st == "Rain": recomendations.append("дождь, не забудь взять зонтик ☔️ или дождевик")
        if st == "Thunderstorm":recomendations.append("гроза, постарайся не выходить на улицу ⛈")
        if int(vd) < 3500: recomendations.append("низкая видимость, осторожнее на дороге 🌫")
        if int(wi['speed']) > 9:recomendations.append("сильный ветер, пострарайся обходить деревья 💨")
        if int(t1) > 15 and st != "Shower rain" and st != "Rain" and st != "Thunderstorm": recomendations.append("тепло, одевайся по-летнему 😎")
        if int(t1) < 14: recomendations.append("прохладно, одевайся потеплее 🧣")
        if int(t1) < 0: recomendations.append("холодно, одевайся тепло 🧣")
        if int(t1) < -10: recomendations.append("мороз, не забудь шапку,шарф и рукавицы 🥶")
        if int(humi) > 80 and st != "Shower rain" and st != "Rain" and st != "Thunderstorm": recomendations.append("повышенная влажность, может начаться дождь 🌧")

        if recomendations:
            recomendation = ',\n'.join(map(str,recomendations))
            recomendation = f"❗️ На улице {recomendation} \n\n"

        else:recomendation = ''

        if st == "Shower rain" or st == "Rain":
            r = w.rain
            rain_value = f'За 1 час выпало {r["1h"]} мм дождя \n\n'

        #Отправляем сообщение с данными по погоде
        bot.reply_to(message,
        		f"┌ Температура воздуха {t4} - {t3} °C  ({t1} °C)\n" +
				f"├ Ощущается как {t2} °C\n" +
				f"├ Скорость ветра {wi['speed']} м/с\n" +
                f"├ Направление ветра {wi['deg']} °\n" +
				f"├ Давление {round(pr/133,2)} мм.рт.ст\n" +
				f"├ Влажность {humi} %\n" +
				f"├ Видимость {vd/1000} км\n" +
				f"├ Облачность {cl} %\n" +
				f"└ {dt[0].capitalize() + dt[1:]} {icons[icon]}\n\n"+
                str(recomendation) +
                str(rain_value)+
				f"Время обновления данных о погоде 🕑 {ti}")

        send_subscribe(message)

    except NotFoundError:
        msg = message.text
        msg = msg.split(' ')
        place = msg[len(msg)-1]
        bot.reply_to(message,f'Место "{place}" не найдено!')

    except TimeoutError:
        bot.send_message(message.chat.id,"Мне очень жаль, но истекло время ожидания ответа от сервера. Разработчик уведомлён и уже работает над этим 👨‍💻")
        bot.send_message(config.ADMIN_ID,"[Error] : (Timeout error)")

    except Exception as e:
        logger.error(e)
        bot.send_message(config.ADMIN_ID,f'[Exception] : ({e})')
        bot.send_message(message.chat.id,"Произошла ошибка, администратор уведомлён. Проверь правильность введённых данных.")

@bot.message_handler(content_types=['text'])
def send_error(message):
    bot.send_message(message.chat.id,f'🤖 Проверь правильность введённой команды, ведь команды "{message.text}" не существует!')

bot.polling(none_stop=True, interval=0)