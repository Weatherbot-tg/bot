import telebot
from pyowm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import NotFoundError
import config
from datetime import datetime
import os

bot = telebot.TeleBot(config.BOT_TOKEN)
icons = {'01':'☀️','02':'🌤','03':'⛅️','04':'☁️','09':'🌧','10':'🌦','11':'⛈','13':'❄️','50':'🌫️'}
recomendation = ''

config_dict = get_default_config()
config_dict['language'] = 'ru'

owm = OWM(config.OWM_TOKEN, config_dict)
mgr = owm.weather_manager()
geo_mgr = owm.geocoding_manager()

@bot.message_handler(commands=['start'])
def welcome(message):
    photo = open(f'{os.path.dirname(os.path.realpath(__file__))}/media/logo-test.png', 'rb')
    bot.send_photo(message.chat.id,photo, '👋 Привет, ' + str(message.from_user.first_name) + '! Меня зовут Weather bot, и я помогу тебе узнавать погоду в любой точке Земли 🌎 в любое время.')
    help(message)

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Ты можешь управлять мной, отправляя эти команды:\n\n/help - команды бота\n/credits - автор бота\n/weather - вывод погоды в указанном городе\n/weather_coords - вывод погоды по географическим координатам\n/weather_zip - вывод погоды по почтовому индексу\n/air_pollution - вывод качества воздуха\n/report - сообщить об ошибке')

@bot.message_handler(commands=['credits'])
def credits(message):
    bot.send_message(message.chat.id, 'Weather bot by Dmitry Karpenko (@dimkarpenko), Russia\nGitHub - https://github.com/Dimkarpenko/Weatherbot')

@bot.message_handler(commands=['weather'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Введите название города')
  bot.register_next_step_handler(sent, send_weather,1)

@bot.message_handler(commands=['weather_coords'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Введите координаты (широта,долгота)')
  bot.register_next_step_handler(sent, send_weather,2)

@bot.message_handler(commands=['weather_zip'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Введите данные в формате (индекс,страна)')
  bot.register_next_step_handler(sent, send_weather,3)

@bot.message_handler(commands=['weather_id'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Введите ID города/населённого пункта')
  bot.register_next_step_handler(sent, send_weather,4)

@bot.message_handler(commands=['id'])
def send_msg(message):
    bot.send_message(message.chat.id, f"Your id is {message.chat.id}")
    a = message.chat.id
    bot.send_message(config.ADMIN_ID, f'{message.chat.username} - {a}')

@bot.message_handler(commands=['report'])
def send_report(message):
    sent = bot.send_message(message.chat.id, 'Введите сообщение')
    bot.register_next_step_handler(sent, send_report)

@bot.message_handler(commands=['air_pollution'])
def send_air(message):
    sent = bot.send_message(message.chat.id, 'Введите координаты (широта,долгота)')
    bot.register_next_step_handler(sent, send_air)

def send_air(message):
    mgr = owm.airpollution_manager()
    msg = message.text
    msg = msg.split(',')
    lat = float(msg[0])
    lon = float(msg[1])
    air_status = mgr.air_quality_at_coords(lat, lon)

    bot.send_message(message.chat.id,
        f"== В точке {lat} , {lon} качество воздуха ==\n"+
        "┌ CO: "+str(air_status.co)+"\n"+
        "├ NO: "+str(air_status.no)+"\n"+
        "├ NO2: "+str(air_status.no2)+"\n"+
        "├ O3: "+str(air_status.o3)+"\n"+
        "├ SO2: "+str(air_status.so2)+"\n"+
        "├ PM2_5: "+str(air_status.pm2_5)+"\n"+
        "├ PM10: "+str(air_status.pm10)+"\n"+
        "├ NH3: "+str(air_status.nh3)+"\n"+
        "└ Качество воздуха: "+str(air_status.aqi)+"\n\n"
        "Время сбора данных 🕑 "+str(air_status.reference_time('iso')))

def send_report(message):
    try:
        bot.send_message(config.ADMIN_ID, f"New report:\nName: {message.from_user.first_name} {message.from_user.last_name}\nUsername: @{message.chat.username}\nMessage: {message.text}\nDate: {datetime.utcfromtimestamp(int(message.date)).strftime('%Y-%m-%d %H:%M:%S')}\nLanguage: {message.from_user.language_code}\nId: {message.chat.id}")
        bot.send_message(message.chat.id,"Ваше сообщение получено, спасибо!")
    except:
        bot.send_message(message.chat.id,"Не удалось отправить сообщение, попробуйте связаться с поддержкой --> @dimkarpenko")
    
def send_weather(message,weather_type):
    try:
        if int(weather_type) == 1:
            msg = message.text
            msg = msg.split(' ')
            place = msg[len(msg)-1]
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

        #Отправляем сообщение с данными по погоде
        bot.send_message(message.chat.id,
                "== Информация о погоде в месте "+ str(place) + " == \n"+
                "┌ В месте " + str(place) + " температура " + str(t1) + " °C" + "\n" +
                "├ Максимальная температура " + str(t3) + " °C" +"\n" +
                "├ Минимальная температура " + str(t4) + " °C" + "\n" +
                "├ Ощущается как " + str(t2) + " °C" + "\n" +
                "├ Скорость ветра " + str(wi['speed']) + " м/с" + "\n" +
                "├ Направление ветра " + str(wi['deg']) + " °" + "\n" +
                "├ Давление " + str(round(pr/133,2)) + " мм.рт.ст" + "\n" +
                "├ Влажность " + str(humi) + " %" + "\n" +
                "├ Видимость "+ str(vd/1000)+ "км" + "\n" +
                "├ Облачность " + str(cl) + " %" + "\n" +
                "└ " + str(dt[0].capitalize() + dt[1:]) + ' ' + str(icons[icon]) +"\n\n"+
                str(recomendation) +
                "Время обновления данных о погоде 🕑 "+ str(ti))

    except NotFoundError:
        msg = message.text
        msg = msg.split(' ')
        place = msg[len(msg)-1]
        bot.send_message(message.chat.id,f'Место "{place}" не найдено!')

    except TimeoutError:
        bot.send_message(message.chat.id,"Мне очень жаль, но истекло время ожидания ответа от сервера. Разработчик уведомлён и уже работает над этим 👨‍💻")
        bot.send_message(config.ADMIN_ID,"[Error] : (Timeout error)")

    except Exception as e:
        print(f'[Exception] : ({e})')
        bot.send_message(config.ADMIN_ID,f'[Exception] : ({e})')
        bot.send_message(message.chat.id,"Произошла ошибка, администратор уведомлён. Приносим свои извинения за предоставленные неудобства.")

@bot.message_handler(content_types=['text'])
def send_error(message):
    bot.send_message(message.chat.id,'🤖 Этот бот в недоумении,так как вы ввели несуществующую команду!')

bot.polling(none_stop=True, interval=0)