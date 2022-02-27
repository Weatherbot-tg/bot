import telebot
from pyowm import OWM
from pyowm.utils.config import get_default_config
import config

bot = telebot.TeleBot(config.BOT_TOKEN)
icons = {'01':'☀️','02':'🌤','03':'⛅️','04':'☁️','09':'🌧','10':'🌦','11':'⛈','13':'❄️','50':'🌫️'}

@bot.message_handler(commands=['start'])
def welcome(message):
	bot.send_message(message.chat.id, '👋 Добро пожаловать, ' + str(message.from_user.first_name) + '! Меня зовут Weather bot, и я помогу вам узнавать погоду в любой точке Земли в любое время.\n\nВы можете управлять мной, отправляя эти команды:\n\n/help - команды бота\n/credits - автор бота\n/weather - вывод погоды в указанном городе')

@bot.message_handler(commands=['help'])
def help(message):
	bot.send_message(message.chat.id, 'Вы можете управлять мной, отправляя эти команды:\n\n/help - команды бота\n/credits - автор бота\n/weather - вывод погоды в указанном городе')

@bot.message_handler(commands=['credits'])
def help(message):
	bot.send_message(message.chat.id, 'Weather bot by Dmitry Karpenko (@dimkarpenko), Russia')

@bot.message_handler(commands=['weather'])
def get_msg(message):
  sent = bot.send_message(message.chat.id, 'Введите название города')
  bot.register_next_step_handler(sent, send_weather)

@bot.message_handler(commands=['id'])
def send_msg(message):
    bot.send_message(message.chat.id, f"Your id is {message.chat.id}")
    a = message.chat.id
    bot.send_message(config.ADMIN_ID, a)

def send_weather(message):
    try:
        msg = message.text
        msg = msg.split(' ')
        place = msg[len(msg)-1]

        config_dict = get_default_config()
        config_dict['language'] = 'ru'

        owm = OWM(config.OWM_TOKEN, config_dict)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(place)
        w = observation.weather

        t = w.temperature("celsius")
        t1 = t['temp']
        t2 = t['feels_like']
        t3 = t['temp_max']
        t4 = t['temp_min']

        wi = w.wind()['speed']
        humi = w.humidity
        cl = w.clouds
        st = w.status
        dt = w.detailed_status
        ti = w.reference_time('iso')
        pr = w.pressure['press']
        vd = w.visibility_distance
        icon = w.weather_icon_name[:-1]

        bot.send_message(message.chat.id,
        		"┌ В городе " + str(place) + " температура " + str(t1) + " °C" + "\n" +
				"├ Максимальная температура " + str(t3) + " °C" +"\n" +
				"├ Минимальная температура " + str(t4) + " °C" + "\n" +
				"├ Ощущается как " + str(t2) + " °C" + "\n" +
				"├ Скорость ветра " + str(wi) + " м/с" + "\n" +
				"├ Давление " + str(round(pr/133,2)) + " мм.рт.ст" + "\n" +
				"├ Влажность " + str(humi) + " %" + "\n" +
				"├ Видимость " + str(vd) + " метров" + "\n" +
				"├ Облачность " + str(cl) + " %" + "\n" +
				"└ " + str(dt.title()) + ' ' + str(icons[icon]) +"\n\n"+
				"Время сбора информации 🕑 "+ str(ti)
				)

    except:
        msg = message.text
        msg = msg.split(' ')
        place = msg[len(msg)-1]
        bot.send_message(message.chat.id,f'Город "{place}" не найден!')

@bot.message_handler(content_types=['text'])
def send_error(message):
    bot.send_message(message.chat.id,'🤖 Этот бот в недоумении,так как вы ввели несуществующую команду!')

bot.polling(none_stop=True, interval=0)