import telebot
import time
import schedule
from transformers import T5ForConditionalGeneration, T5Tokenizer # переводчик
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM # проверка орфографии
from telebot import types

def translate(text,prefix):
    src_text = prefix + text
    input_ids = tokenizer1(src_text, return_tensors="pt")
    generated_tokens = model1.generate(**input_ids)
    return tokenizer1.batch_decode(generated_tokens, skip_special_tokens=True)

def check(text):
    inputs = tokenizer2(text, max_length=None, padding="longest", truncation=False, return_tensors="pt")
    outputs = model2.generate(**inputs, max_length = inputs["input_ids"].size(1) * 1.5)
    return tokenizer2.batch_decode(outputs, skip_special_tokens=True)

model_name1 = 'utrobinmv/t5_translate_en_ru_zh_small_1024'
model1 = T5ForConditionalGeneration.from_pretrained(model_name1)
tokenizer1 = T5Tokenizer.from_pretrained(model_name1)

tokenizer2 = AutoTokenizer.from_pretrained("ai-forever/sage-fredt5-large")
model2 = AutoModelForSeq2SeqLM.from_pretrained("ai-forever/sage-fredt5-large")

bot = telebot.TeleBot('YOUR TOKEN')

user_states = {}
strana = ['Русский','Английский','Китайский']
mark = ['translate to ru:','translate to en: ','translate to zh: ']

def create_keyboard(strana=strana,mark=mark):
    keyboard = types.InlineKeyboardMarkup(); #наша клавиатура
    for country, sokr in zip(strana,mark):
        key_yes = types.InlineKeyboardButton(text=country, callback_data=sokr)
        keyboard.add(key_yes) #добавляем кнопку в клавиатуру
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, "Привет, напиши /help, чтобы узнать что я умею.")

@bot.message_handler(commands=['help'])
def send_help(message):
	bot.reply_to(message, "Вот что я умею: \n /translate - для перевода текста \n /check - для проверки текста на ошибки")

@bot.message_handler(commands=['check'])
def ask_text_for_check(message):
    user_states[message.chat.id] = {}
    bot.send_message(message.chat.id, "Отправь текст на русском, который нужно проверить.")
    bot.register_next_step_handler(message, check_text)

@bot.message_handler(commands=['translate'])
def ask_lang(message):
    user_states[message.chat.id] = {}
    question = "Выбери на какой язык нужно перевести текст."
    bot.send_message(message.chat.id, text=question, reply_markup=create_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_language_selection(call):
    chat_id = call.message.chat.id
    if 'prefix' not in user_states[chat_id]:
        user_states[chat_id]['prefix'] = call.data
        bot.send_message(call.message.chat.id, 'Теперь скинь мне текст, который нужно перевести. Текст должен быть написан на русском, английском или китайском.')
        bot.answer_callback_query(call.id)
    else:
        bot.send_message(call.message.chat.id,'Попробуй ещё раз. /translate')
    
@bot.message_handler(content_types=['text'])
def last_step_translate(message):
    chat_id = message.chat.id
    user_state = user_states.get(chat_id)
    
    if user_state and 'prefix' in user_state:
        prefix = user_states[chat_id]['prefix']
        text = message.text
        translation = translate(text,prefix)
        bot.send_message(message.from_user.id, translation[0])
        bot.send_message(message.chat.id,'Если хочешь перевести что-то ещё напиши /translate или /help для просмотра других функций')
        user_states[chat_id] = {}
    else:
        bot.send_message(message.from_user.id, 'Вы не выбрали язык. Попробуйте снова. Используйте /translate')

@bot.message_handler(content_types=['text'])
def check_text(message):
    chat_id = message.chat.id
    text = message.text
    cheking = check(text)
    bot.send_message(message.from_user.id, cheking[0])
    bot.send_message(message.chat.id,'Если хочешь проверить что-то ещё напиши /check или /help для просмотра других функций')
    
bot.infinity_polling()
