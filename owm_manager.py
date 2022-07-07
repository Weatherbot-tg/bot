from pyowm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import NotFoundError

import text

class OwmMGR:
    def __init__(self,api_key,lang):
        self.config_dict = get_default_config()
        self.config_dict['language'] = lang
        self.owm = OWM(api_key, self.config_dict)
        self.mgr = self.owm.weather_manager()
        self.geo_mgr = self.owm.geocoding_manager()
        self.uv_mgr = self.owm.uvindex_manager()
        self.air_mgr = self.owm.airpollution_manager()

    def handle_weather(self,place,weather_type):
        try:
            if int(weather_type) == 1:
                observation = self.mgr.weather_at_place(place)
                weather = observation.weather

            elif int(weather_type) == 2:
                place = place.split(',')
                weather = self.mgr.weather_at_coords(float(place[0]), float(place[1])).weather 
                list_of_locations = self.geo_mgr.reverse_geocode(float(place[0]), float(place[1]))
                place = list_of_locations[0].name

            elif int(weather_type) == 3:
                place = place.split(',')
                weather = self.mgr.weather_at_zip_code(str(place[0]),str(place[1])).weather
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
    
    def handle_air(self,lat,lon):
        air_status = self.air_mgr.air_quality_at_coords(float(lat), float(lon))

        return(f"┌ CO: {air_status.co}\n"+
                f"├ NO: {air_status.no}\n"+
                f"├ NO2: {air_status.no2}\n"+
                f"├ O3: {air_status.o3}\n"+
                f"├ SO2: {air_status.so2}\n"+
                f"├ PM2_5: {air_status.pm2_5}\n"+
                f"├ PM10: {air_status.pm10}\n"+
                f"├ NH3: {air_status.nh3}\n"+
                f"└ {text.send_air_text} {air_status.aqi}\n\n"
                f"{text.last_receive_data_text} {air_status.reference_time('iso')}")

    def check_exist(self,place):
        try:
            observation = self.mgr.weather_at_place(place)
            return True
        
        except:
            return False

    def handle_uv(self,lat,lon):
        uvi = self.uv_mgr.uvindex_around_coords(float(lat), float(lon))
        ref_time = uvi.reference_time('iso')
        return f'{text.send_uv_text_1}{uvi.value}{text.send_uv_text_1}{ref_time}'

    def handle_geo(self,place,country):
        list_of_locations = self.geo_mgr.geocode(place, country=country, limit=1)
        return f"{text.send_to_geo_text_1}{list_of_locations[0].lat}, {text.send_to_geo_text_2}{list_of_locations[0].lat}"
