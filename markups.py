from aiogram import types
import text,config

buttons = types.InlineKeyboardMarkup()
btn_sub_1 = types.InlineKeyboardButton(text=text.btn_sub_1_text, url=config.SUBSCRIBE_LINK)
btn_sub_2 = types.InlineKeyboardButton(text=text.btn_sub_2_text, url=config.SUBSCRIBE_LINK)
buttons.add(btn_sub_1,btn_sub_2)

donate_buttons = types.InlineKeyboardMarkup()
btn_donate = types.InlineKeyboardButton(text=text.btn_donate_text, url=config.DONATE_LINK)
donate_buttons.add(btn_donate)

subscribe_button = types.InlineKeyboardMarkup()
btn_subscribe = types.InlineKeyboardButton(text=text.subscribe_btn_text, callback_data='subscribe_weather')
subscribe_button.add(btn_subscribe)

subscribed_buttons = types.InlineKeyboardMarkup()
btn_unsubscribe = types.InlineKeyboardButton(text=text.unsubscribe_btn_text, callback_data='unsubscribe_weather')
btn_edit = types.InlineKeyboardButton(text=text.edit_btn_text, callback_data='edit_weather')
subscribed_buttons.add(btn_unsubscribe,btn_edit)