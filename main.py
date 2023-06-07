import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
import spotipy
from spotipy import SpotifyOAuth
import re

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
# авторизуем бота через его аккаунт Спотифай
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI))


@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.answer('Привет!\nЯ - бот, превращающий фразы в плейлисты!')
    await message.answer('Чтобы создать плейлист напишите мне любую фразу. '
                         'Предложение будет разбито на слова, названиями треков '
                         'в плейлисте и будут эти слова.')
    await message.answer('Чтобы посмотреть пример используйте /example.\n'
                         'Если возникнут проблемы, используйте /help.')


@dp.message_handler(commands=['example'])
async def search_example(message: types.Message):
    example_1 = types.InputFile('examples/example_1_1.jpg')
    example_2 = types.InputFile('examples/example_1_2.jpg')
    await message.answer_media_group([types.InputMediaPhoto(example_1), types.InputMediaPhoto(example_2)])
    await message.answer('Пример написания фразы.')


@dp.message_handler(commands=['help'])
async def information(message: types.Message):
    await message.answer('Чтобы посмотреть пример используйте /example.')
    await message.answer('Если не удаётся создать плейлист по выбранной фразе, '
                         'вы можете попробовать объединить слова, которые по вашему мнению '
                         'имеют большую вероятность оказаться в названии песни вместе, чем по '
                         'отдельности, при помощи символа "+".\nНапример, вероятность найти '
                         'треки с названиями "Уолтер" и "Уайт" очень мала, но используя '
                         'символ объединения "+" вы можете произвести поиск трека '
                         'с названием "Уолтер Уайт", который уже вполне вероятно встретится. '
                         'Запрос к боту будет выглядеть, например, так: "Уолтер+Уайт - мой '
                         'лучший+друг".\n'
                         'Небуквенные символы в предложении не учитываются.')


@dp.message_handler()
async def create_playlist(message: types.Message):
    start_msg = await message.answer('Выполняется подбор треков...')
    tracks_uris = []
    playlist_completed = True
    missing_track = None
    # удаляем из фразы все небуквенные символы, кроме "+"
    phrase = re.sub(r'[^\w\s+]', '', message.text)
    # разбиваем фразу(словосочетание со знаком "+" запишется, как один элемент)
    words = phrase.split()
    # в словосочетаниях со знаком "+" заменяем его на пробел
    for i in range(len(words)):
        words[i] = words[i].replace('+', ' ')
    # проходимся по каждому слову(словосочетанию)
    for track_name in words:
        track_found = False
        # Спотифай позволяет выводить не более 50 треков за раз, поэтому проходимся по ним в цикле со сдвигом
        for offset in range(0, 300, 50):
            results = sp.search(q=track_name, limit=50, offset=offset, type='track')
            if results['tracks']['items']:
                for track in results['tracks']['items']:
                    # сравнение происходит без учёта регистра
                    if track['name'].lower() == track_name.lower():
                        tracks_uris.append(track['uri'])
                        track_found = True
                        break
                if track_found:
                    break
            else:
                playlist_completed = False
                missing_track = track_name
                break
        # после просмотра 300 треков проверяем, удалось ли найти подходящий
        if not track_found:
            playlist_completed = False
            missing_track = track_name
            # если один из треков не найден, то прерываем поиск остальных
            break

    if playlist_completed:
        playlist = sp.user_playlist_create(
            sp.current_user()['id'],
            name=message.text.replace('+', ' '),
            public=True)
        sp.playlist_add_items(playlist['id'], tracks_uris)
        await start_msg.edit_text(f'Плейлист успешно создан!\n{playlist["external_urls"]["spotify"]}')
    else:
        await start_msg.edit_text('Не удалось подобрать подходящие треки.\n'
                                  f'Ненайденный трек: "{missing_track}".')
        await message.answer('Используйте /help, чтобы получить подсказки по поиску.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
