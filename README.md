# Русификация Oxenfree 2 Lost Signals

## Как поучаствовать в переводе

### [Таблица, где обитают переводчики](https://docs.google.com/spreadsheets/d/1JOsjxT02BRCuS6lXw53ev5KbCGqm-FSbToUkVA1gNF8)
### [Тред на Zone of Games](https://forum.zoneofgames.ru/topic/73375-oxenfree-2)

- Запросить у **Lenferd** доступ к таблице
- Отметиться на форуме, перевод какого раздела интересует - чтобы не конфликтовать с другими
переводчиками
- Переводить, следуя наставлениям в таблице

Инструкция по изготовлению собственных бандлов для русификатора приведена ниже, в разделе
"инструменты для перевода"

## Структура файлов в репозитории

Переведённый текст лежит в файлах `.json` в папке `localization/`:
- `bundle`: из какого .bundle файла получен текст
- `scene`: кодовое имя "сцены" в которой происходит диалог; идентично имени файла и связано с именем
MonoBehaviour в ассетах игры
- `entries`: все строчки диалога, текста, надписей в меню и прочего
    - `tag`: тег, по которому игра ищет переведённые строчки в базе локализации
    - `en`: оригинальный текст на английском
    - `ru_final`: полноценный перевод текста на русский
    - `verified`: на перевод посмотрели живые переводчики, и сказали "норм"
    - `ru_native`: оригинальный русский текст, оставшийся в игре (там где есть)
    - `ru_machine`: машинный перевод (выполнен с помощью http://deepl.com)
    - `uk`: украинский текст, как маркер наличия и пример официального перевода

> ℹ Не стоит переводить файлы из `localization/` напрямую в репозитории - самая актуальная
> версия перевода находится в таблице.

В `src/oxenfree/` лежат скрипты на Python, используемые для извлечения текстов из игры,
импорта переводов из CSV-файлов и многого другого.

В `src/textrepack/` лежат исходники утилиты на C#, предназначенной для редактирования
файлов `.bundle`. Используемый в скриптах UnityPy, к сожалению, намертво убивает некоторые
бандлы в процессе перепаковки. Собранная утилита `textrepack.exe` лежит в корне репозитория.

Если вам кажется, что в коде что-то не то - пулл-реквесты приветствуются.

## Как работать с инструментами для перевода

> ❗ ***ВАЖНО: все скрипты сохраняют результаты работы в папку, передаваемую параметром
> `--output-dire` (по-умолчанию - `output/<имя_скрипта>/`),  удаляя перед этим всё её
> содержимое ! Не держите там ничего ценного.***

### I. Подготовить окружение для работы

0. Скачать и распаковать архив с проектом

![how to zip](https://github.com/kryakozebra/oxenfree2_rus_dev/assets/139701511/1c1fe8a0-c419-436d-8ed5-639956a6f7d9)

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

4. Установить проект и его зависимости:
```
python -m pip install -e . -r requirements.txt
```

5. Запустить программу для перепаковки `.bundle`-файлов и убедиться, что она работает:
```
textrepack
```
Должно высветить в консоли текст `usage: textrepack ...`; если этого не произошло - скорее
всего, у вас какие-то проблемы с .Net Framework (Google в помощь).

### II. Импортировать данные из таблицы переводов

> ℹ Если вы не вносили изменения таблицу - скорее всего, вам нужно пропустить этот шаг.

1. Открыть в таблице лист `loc_packages`, сохранить его как tab separated values:

![how to get csv](https://github.com/kryakozebra/oxenfree2_rus_dev/assets/139701511/374b7299-2820-4f05-b3db-54fe7d904468)

Повторить процедуру для листа `dialogue_packages`.

> _**Важно:** названия файлов должны содержать слова `loc` и `dialogue` соответственно;
> и лучше использовать имена без пробелов._

2. Импортировать переводы из csv (используя имена скачанных файлов):
```
prepare_jsons --csv input\loc_packages.csv input\dialogue_packages.csv --csv-format lenferd --patch localization
```
Флаг `--patch <папка>` позволяет изменить только поле `ru_final`. Если хочется сгенерировать
все `.json`-файлы заново - флаг можно убрать.

### III. Запаковать новые бандлы

2. Запустить скрипт перепаковки:
```
repack_bundle --game-dir "E:\games\Oxenfree II Lost Signals" --translations-dir output\prepare_jsons\
```
После недолгого жужжания, в папке `output/repack_bundles/` должны появиться два файла:
`dialogue_packages_assets_all.bundle` и `loc_packages_assets_.bundle`. Их можно смело
копировать в
`<папка с игрой>/Oxenfree2_Data/StreamingAssets/aa/StandaloneWindows64/`.

Если предыдущий этап (ипморт таблицы) был пропущен - во флаг `--translations-dir`
стоит передавать папку `localization`. Это сгенерирует бандлы с переводом из текущих
файлов в репозитории.

## Разработчику

### Как выдрать текст из Oxenfree 2 и воткнуть его обратно.

> (a.k.a, как начать жизнь с нуля)

1. Распаковать текст из ассетов игры:
```
unpack_bundle.py --game-dir "E:\games\Oxenfree II Lost Signals"
```
Появится файл `output/unpack_bundle/text_table.csv` с таблицей всего текста в игре. Если
хочется ужаснуться - можно открыть его в Excel, импортировать в Google Docs / Excel Web,
или редактировать в Notepad++ или другом продвинутом редакторе.
> Сообщения `WARNING:oxenfree.bundle:bundle: failed to read typetree; some object skipped` - это
> нормально; у используемой библиотеки UnityPy аллергия на бандл
> `dialogue_packages_assets_all`.

2. Превратить одну большую таблицу в много маленьких файликов
```
prepare_jsons.py --csv output/unpack_bundle/text_table.csv --csv-format bundle
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
