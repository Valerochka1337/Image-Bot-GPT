from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import Dispatcher
import pandas as pd
import re
import openai
from json import loads, dumps
from datetime import timedelta

# Set up OpenAI API credentials
openai.api_key = "YOUR_TOKEN"

storage = MemoryStorage()
bot = Bot("YOUR_TOKEN")
dp = Dispatcher(bot, storage=storage)


class ClientStatesGroup(StatesGroup):
    gen_img = State()


# Load users data from CSV file or create an empty DataFrame
users = pd.read_csv("users.csv", index_col=0)

IMAGE_CHATGPT_PREFIX = """
Image ChatGPT is designed to be able to assist with a wide range of text and visual related tasks

Image ChatGPT is able to respond to a human with text and visual information.

Since Image ChatGPT is a language model it cannot directly generate images. However, it can use a special tool to
 indicate a picture appearance in the response

This is FORMAT OF A TOOL: [IMAGE]{description of the image}

This is user message:
{'
"""

IMAGE_CHATGPT_SUFFIX = """
'}
Image ChatGPT is facing a real human, who thinks that it can provide him with images by itself.
 However, you can just use a special tool.

Special tool format: [IMAGE]{description of the image}

REMEMBER to use a tool with your own image description, which is based on the user's request

Your image description SHOULD be DETAILED
"""
self_messages = [{"role": "system", "content": "You are a helpful assistant, who speaks russian"}]


def generate_image(description):
    """
    Generates an image URL based on the given description using OpenAI Image API.

    :param description: Description of the image to be generated.
    :return: Image URL.
    """
    img_response = openai.Image.create(
        prompt=description,
        n=1,
        size="1024x1024"
    )
    image_url = img_response['data'][0]['url']
    return image_url


def parse_response(text):
    """
    Parses the response text and extracts data related to text and images.

    :param text: Response text from OpenAI Chat API.
    :return: Dictionary containing the extracted data.
    """
    pattern = r"\[IMAGE\]\{(.+)\}"
    matches = re.findall(pattern, text)
    result = {"data": []}
    parts = re.split(pattern, text)

    for part in parts:
        if part in matches:
            if len(part) > 1:
                result["data"].append({"type": "image", "content": part})
        elif part:
            if len(part) > 1:
                result["data"].append({"type": "text", "content": part})

    return result


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    """
    Handler for the "/start" command.
    Sends a welcome back message if the user is registered, otherwise registers the user and sends a welcome message.
    """
    global users
    user_id = message.from_user.id

    if user_id in users.index:
        await bot.send_message(message.chat.id, "И снова здравствуй, " + message.from_user.first_name + "!")
    else:
        users.loc[user_id] = [2000, 0, message.date, 2000, 0, dumps([])]
        await bot.send_message(message.chat.id, "Привет, " + message.from_user.first_name + "!")


@dp.message_handler(commands=["get_tokens"])
async def get_tokens_command(message: types.Message):
    """
    Handler for the "/get_tokens" command.
    Increases the token capacity of the user if a cooldown period has passed since the last increase.

    :param message: The message object.
    """
    global users
    user_id = message.from_user.id

    if not (user_id in users.index):
        await bot.send_message(message.chat.id, "К сожалению, я вас не знаю, введите команду /start")
    else:
        if pd.to_datetime(users.loc[user_id, 'last_date']) + timedelta(seconds=30) > message.date:
            await bot.send_message(message.chat.id,
                                   "Вы превысили лимит по пополнению токенов."
                                   " Вы сможете его восстановить не более, чем через 3 минуты")
            return

        users.loc[user_id, 'tokens'] = 0
        users.loc[user_id, 'last_date'] = message.date

    await bot.send_message(message.chat.id, message.from_user.first_name + ", вы пополнили запас токенов!")


@dp.message_handler(commands=["get_pic"])
async def pic_command(message: types.Message):
    """
    Handler for the "/get_pic" command.
    Asks the user to provide a description of the image they want to generate.

    :param message: The message object.
    """
    await message.answer_chat_action("typing")
    global users
    user_id = message.from_user.id

    if not (user_id in users.index):
        await bot.send_message(message.chat.id, "К сожалению, я вас не знаю, введите команду /start")
    else:
        await ClientStatesGroup.gen_img.set()

    await bot.send_message(message.chat.id,
                           message.from_user.first_name + ", напишите описание картинки,"
                                                          " которую вы хотите сгенерировать")


@dp.message_handler(state=ClientStatesGroup.gen_img)
async def generate_pic(message: types.Message, state: FSMContext):
    """
    Handler for generating an image based on the user's description.

    :param message: The message object.
    :param state: FSM context state.
    """
    try:
        await message.answer_chat_action("upload_photo")
        image_url = generate_image(message.text)
        await bot.send_photo(message.chat.id, image_url)
    except Exception as e:
        print(e)  # Print error for debugging purposes
        await bot.send_message(message.chat.id, "Что-то пошло не так")

    await state.finish()


@dp.message_handler()
async def respond(message: types.Message):
    """
    Default handler for responding to user messages.

    :param message: The message object.
    """
    # Typing animation
    await message.answer_chat_action("typing")
    user_id = message.from_user.id

    # If user is not registered, notify and exit
    if not (user_id in users.index):
        await message.reply("Ты еще не поздоровался, ничем не могу помочь")
        return

    # If user has enough tokens
    if users.loc[user_id, 'tokens'] < users.loc[user_id, 'token_capacity']:
        # If user context is too large, remove older messages
        context = loads(users.loc[user_id, 'context'])
        new_message = [{'role': 'user', 'content': message.text}]
        while users.loc[user_id, 'context_len'] > users.loc[user_id, 'context_capacity']:
            context = context[1:]
            users.loc[user_id, 'context_len'] -= len(context[0]["content"])

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=self_messages + context + [
                    {"role": "system", "content": IMAGE_CHATGPT_PREFIX}] + new_message + [
                             {"role": "system", "content": IMAGE_CHATGPT_SUFFIX}],
                max_tokens=500,
                temperature=0.5,
            )

            users.loc[user_id, 'tokens'] += response["usage"]["total_tokens"]
            users.loc[user_id, 'context'] = dumps(
                context + new_message + [{'role': 'assistant', 'content': str(response.choices[0].message['content'])}],
                ensure_ascii=False)
            users.loc[user_id, 'context_len'] += len(message.text) + len(response.choices[0].message["content"])
            response_msg = response.choices[0].message["content"]

            for el in parse_response(response_msg)["data"]:
                if el["type"] == "text":
                    await message.answer_chat_action("typing")
                    await bot.send_message(message.chat.id, el['content'])
                else:
                    await message.answer_chat_action("upload_photo")
                    await bot.send_photo(message.chat.id, generate_image(el['content']))
        except Exception as e:
            print(e)  # Print error for debugging purposes
            await message.reply("Извините, слишком большая нагрузка, попробуйте позже")

    else:
        await message.reply("У вас закончился лимит по токенам, обновите их")


if __name__ == '__main__':
    executor.start_polling(dp)

# Save users data to CSV file after execution
users.to_csv("users.csv")
