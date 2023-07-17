# Русификация Oxenfree 2 Lost Signals

[Тред на Zone of Games](https://forum.zoneofgames.ru/topic/73375-oxenfree-2)

Переводимый текст лежит в файлах `.json` в папке `localization/`. Структура файлов:
- `bundle`: из какого .bundle файла получен текст
- `scene`: кодовое имя "сцены" в которой происходит диалог; идентично имени файла и связано с именем
MonoBehaviour в ассетах игры
- `entries`: все строчки диалога, текста, надписей в меню и прочего
    - `tag`: тег, по которому игра ищет переведённые строчки в базе локализации
    - `en`: оригинальный текст на английском
    - `ru_final`: полноценный перевод текста на русский
    - `verified`: на перевод посмотрел живой переводчик, и сказал "норм"
    - `ru_native`: оригинальный русский текст, оставшийся в игре (там где есть)
    - `ru_machine`: машинный перевод (выполнен с помощью http://deepl.com)
    - `uk`: украинский текст, как маркер наличия и пример официального перевода

## Как поучаствовать в переводе
- Выбираем понравившийся файл в `localization/`
- Пишем перевод в поле `ru_final` или правим существующий
- В поле `verified` меняем `false` на `true`
- Делаем пулл-реквест

Порядок выбора понравившегося файла:
- В первую очередь, стоит посмотреть на то, у чего есть `ru_final` но нет `verified` -
там перевод вроде как есть, но что-то переводчиков смущает.
- Затем на то, у чего есть `ru_machine` и нет `ru_final` - там только машинный перевод,
который наверняка стоит причесать
- Наконец на то, у чего есть `ru_native` и нет `ru_machine` - это переводы доставшиеся
в наследство от разработчиков, которые могут не соответствовать реальному тексту.
- При этом не стоит уделять много внимания тому, у чего нет `uk` - скорее всего,
это устаревший текст, который остался в файлах но не попал в итоговую игру.

> TODO: добавить картинок с пояснениями для незнакомых с гитхабом

## Как работать с инструментами для перевода

> ❗ ***ВАЖНО: все скрипты по-умолчанию сохраняют результаты работы  в папку `output/<имя_скрипта>`,
> удаляя перед этим содержимое папки! Не держите там ничего ценного.***

Для начала нужно подготовить окружение для работы.

0. Скачать и распаковать архив с проектом

1. Скачать и установить Python (проверялось на 3.11) - https://www.python.org/downloads/

2. Открыть консоль и перейти в папку с проектом:
```
E:
cd E:\git\oxenfree2_rus_dev
```

3. Подготовить локальное окружение Python в папке:
```
python -m venv venv
.\venv\Scripts\activate.bat
```

4. Установить проект и библиотеки для работы с Unity:
```
python -m pip install -e . -r requirements.txt
```

5. Запустить программу для перепаковки `.bundle` файлов и убедиться, что она работает:
```
textrepack
```
Должно высветить в консоли текст `usage: textrepack ...`; если этого не произошло - скорее
всего, у вас какие-то проблемы с .Net Framework (Google в помощь).

### Как сделать собственный русификатор

1. Перевести понравившиеся тексты в `localization/` (см. выше), сохранить файлы.

2. Запустить скрипт перепаковки:
```
repack_bundle --game-dir "E:\games\Oxenfree II Lost Signals" --translations-dir localization/
```
После недолгого жужжания, в папке `output/repack_bundles/` должны появиться два файла:
`dialogue_packages_assets_all.bundle` и `loc_packages_assets_.bundle`.

3. Перенести полученные бандлы в
`<папка с игрой>/Oxenfree2_Data/StreamingAssets/aa/StandaloneWindows64/`.

## Разработчику

### Как выдрать текст из Oxenfree 2 и воткнуть его обратно.

> (a.k.a, как начать жизнь с нуля)

1. Распаковать текст из ассетов игры:
```
unpack_bundle.py --game-dir "E:\games\Oxenfree II Lost Signals"
```
Появится файл `output/unpack_bundle/text_table.csv` с таблицей всего текста в игре. Если хочется
ужаснуться - можно открыть его в Excel, импортировать в Google Docs / Excel Web, или редактировать
в Notepad++ или другом продвинутом редакторе.
> Сообщения `WARNING:oxenfree.bundle:bundle: failed to read typetree; some object skipped` - это
> нормально; у используемой библиотеки UnityPy аллергия на бандл
> `dialogue_packages_assets_all`.

2. Превратить одну большую таблицу в много маленьких файликов
```
prepare_jsons.py --csv output/unpack_bundle/text_table.csv
```
В `output/prepare_jsons/` появится 1000 с гаком файлов `.json`, которые послужат заготовками для дальнейшего перевода.

3. Перевести что-нибудь вручную. Или запустить автопереводчик:
```
autotranslate_jsons --translations-dir output/prepare_jsons/
```
Через полчасика в `output/autotranslate_jsons/` появятся скопированные файлы, у которых в поле
`ru_machine` будет машинный перевод от DeepL.

4. Собрать все интересующие файлы в какую-нибудь папку `input/repack/` и запаковать их обратно в
`.bundle`-файл:
```
repack_bundle --game-dir "E:\games\Oxenfree II Lost Signals" --translations-dir input\repack\
```
Появится файл `output/repack_bundle/loc_packages_assets_.bundle`. Весит он в несколько раз
больше оригинала - потому что при перепаковке теряется алгоритм сжатия.
> Сообщения `<tag> found but no valid translation present in map` - _наверное, тоже нормально,_
> но свидетельствует о наличии странных текстов среди файлов игры.

5. Скопировать бандлы из `output/repack_bundles/` в папку с игрой.

### Как обновить `textrepack`

0. Поставить .NET Core SDK 6: https://dotnet.microsoft.com/en-us/download

1. Подредактировать нужное в `src/textrepack/`

2. Собрать дебаг
```
cd src/textrepack/
dotnet build
mv bin\Release\net6.0\textrepack.exe ..\..\
```
или релиз
```
cd src\textrepack\
dotnet publish --configuration Release --runtime win-x64 --no-self-contained -p:PublishSingleFile=true -p:GenerateFullPaths=true -consoleloggerparameters:NoSummary
mv bin\Release\net6.0\win-x64\publish\textrepack.exe ..\..\
```
