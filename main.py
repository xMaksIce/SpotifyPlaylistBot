import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
import spotipy
from spotipy import SpotifyOAuth

load_dotenv()
bot = Bot(token=os.getenv('API_TOKEN'))
dp = Dispatcher(bot)
# авторизуем бота через его аккаунт Спотифай
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv('CLIENT_ID'),
                                               client_secret=os.getenv('CLIENT_SECRET'),
                                               redirect_uri=os.getenv('REDIRECT_URI')))


@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.answer('Привет!\nЯ - бот, превращающий фразы в плейлисты!')
    await message.answer('Чтобы создать плейлист напишите мне любую фразу. '
                         'Предложение будет разбито на слова, названиями треков '
                         'в плейлисте и будут эти слова.')
    await message.answer('Если возникнут проблемы, используйте /help.')


@dp.message_handler(commands=['help'])
async def information(message: types.Message):
    await message.answer('Если не удаётся создать плейлист по выбранной фразе, '
                         'вы можете попробовать объединить слова, которые по вашему мнению '
                         'имеют большую вероятность оказаться в названии песни вместе, чем по '
                         'отдельности, при помощи символа "+".\nНапример, вероятность найти '
                         'треки с названиями "Уолтер" и "Уайт" очень мала, но используя '
                         'символ объединения "+" вы можете произвести поиск трека '
                         'с названием "Уолтер Уайт", который уже вполне вероятно встретится. '
                         'Запрос к боту будет выглядеть, например, так: "Уолтер+Уайт мой '
                         'лучший+друг".')


@dp.message_handler()
async def create_playlist(message: types.Message):
    tracks_uris = []
    playlist_completed = True
    words = message.text.split(' ')
    for i in range(len(words)):
        words[i] = words[i].replace('+', ' ')
    for track_name in words:
        track_found = False
        for offset in range(0, 300, 50):
            results = sp.search(q=track_name, limit=50, offset=offset, type='track')
            if results['tracks']['items']:
                for track in results['tracks']['items']:
                    if track['name'].lower() == track_name.lower():
                        tracks_uris.append(track['uri'])
                        track_found = True
                        break
                if track_found:
                    break
            else:
                playlist_completed = False
                break

    if playlist_completed:
        playlist = sp.user_playlist_create(
            sp.current_user()['id'],
            name=message.text.replace('+', ' '),
            public=True)
        sp.playlist_add_items(playlist['id'], tracks_uris)
        await message.answer(f'Плейлист успешно создан!\n{playlist["external_urls"]["spotify"]}')
    else:
        await message.answer('Не удалось подобрать подходящие треки.')
        await message.answer('Используйте /help, чтобы получить подсказки по поиску.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
