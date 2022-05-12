import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from lyricsgenius import Genius

# API_TOKEN =
# GENIUS_TOKEN =

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
genius = Genius(GENIUS_TOKEN)


class BotStates(StatesGroup):
    choosing = State()
    waiting_for_song_name = State()


@dp.message_handler(commands=["help"], state="*")
async def help_message(message: types.Message):
    await message.answer('Напиши "отмена" для отмены выбора песни')


@dp.message_handler(lambda m: m.text.startswith("отмена"), state="*")
async def search(message: types.Message, state: FSMContext):
    await message.answer("Действие отменено \n"
                         "В любой момент можешь написать название песни и я найду её текст для тебя")
    await state.reset_state()
    await BotStates.waiting_for_song_name.set()


@dp.message_handler(state=BotStates.waiting_for_song_name)
async def search(message: types.Message, state: FSMContext):
    # artist = genius.search_artist(message.text, max_songs=1, sort="popularity")
    results = genius.search(search_term=message.text, per_page=5)

    result_message = ""
    songs = []

    for count, result in enumerate(results["hits"]):
        result_message += f"{count + 1}. {result['result']['full_title']} \n"
        songs.append(result['result']['full_title'])

    await message.answer(f"Вот что я нашел по запросу {message.text}:\n"
                         f"\n{result_message}\n"
                         f"Напиши мне номер песни ()")
    await state.update_data(songs=songs)
    await BotStates.choosing.set()


@dp.message_handler(state=BotStates.choosing)
async def search(message: types.Message, state: FSMContext):

    if message.text.isdigit():
        songs = list((await state.get_data())['songs'])
        if 1 <= int(message.text) <= 5:
            song = genius.search_song(title=songs[int(message.text) - 1])
            lyrics = str(song.lyrics)
            await message.answer(lyrics)
            await state.reset_state()
            await BotStates.waiting_for_song_name.set()
        else:
            await message.answer("Неправильная цифра!")
    else:
        await message.answer("Это не цифра!")


@dp.message_handler(commands=["start"])
async def help_message(message: types.Message):
    await BotStates.waiting_for_song_name.set()
    await message.answer("Привет, я могу отправить тебе текст любой песни! "
                         "Просто напиши мне ее название и наслаждайся текстом!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
