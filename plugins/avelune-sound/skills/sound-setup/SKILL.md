---
name: sound-setup
description: "Установить и проверить звуковые инструменты avelune-sound: ffmpeg, библиотеку реальных звуков, earshot. Подключить свою папку со звуками, настроить докачку звуков по плану ролика (Sonniss GDC, Freesound, Kenney) и оценку качества записей. Использовать, когда просят настроить, починить или проверить звук-плагин, или doctor.py вернул не READY."
argument-hint: "[что настроить: всё, библиотеку, earshot]"
---

# Настройка звуковых инструментов

Скрипты: `SETUP = ${CLAUDE_SKILL_DIR}/scripts`, `RSFX = ${CLAUDE_SKILL_DIR}/../real-sfx/scripts`.

## 1. Диагноз

```
python "SETUP/doctor.py"          # --json для машинного чтения, --net проверит доступ к api.openverse.org
```
Последняя строка `STATUS:` говорит, что делать: `BLOCKED` (нет ffmpeg/Python), `NO_LIBRARY` (нет реальных записей), `LIMITED` (нет «ушей»: earshot или теги YAMNet), `READY`. Строки `next:` дают готовые команды под систему пользователя. Команды установки программ (winget, brew, uv) запускай только после согласия пользователя.

## 2. Библиотека реальных звуков (без неё озвучки нет)

Всё, что настраивается, хранится в `~/.avelune-sound/real-sfx/` (config.json, индекс, вкус, модели). Папку плагина Claude Code заменяет при каждом обновлении, а эту папку не трогает. Другое место можно задать переменной `REAL_SFX_HOME`.

**Своя папка.** Найди папки, похожие на звуковые паки, и подключи только паки эффектов (без музыки и превью):
```
python "RSFX/setup.py" scan "D:/Sounds"
python "RSFX/setup.py" add-library montage "D:/Sounds/SFX" --tier main --index
python "RSFX/setup.py" add-library old_packs "F:/packs" --tier extra --index     # запасная: только где в main нет звука
python "RSFX/setup.py" check
```
Если пользователь не знает, где лежат звуки, ищи папки с 20 и больше файлов wav/mp3/ogg/flac в Downloads, Music, Documents и на других дисках. Паки для монтажа обычно называются `sfx`, `звуки`, `zvukogram`, `mixkit`, `пак`.

**Звуки по плану, без своей библиотеки** (основной путь для ролика, его ведёт `video-sound`, шаг 3). Агент пишет план звуков ролика, и скрипт скачивает ровно эти файлы по одному из трёх профессиональных бесплатных библиотек:
```
python "SETUP/fetch.py" template > work/sound_plan.json      # формат плана
python "SETUP/fetch.py" search impact soft --role hit         # что найдётся по словам, до скачивания
python "SETUP/fetch.py" plan work/sound_plan.json --register  # скачать по плану, оценить, подключить
python "SETUP/sources.py" status                              # какие источники включены
```
- **Sonniss GDC** (все годы бандла, около 75 архивов): студийные WAV, коммерческое использование без указания авторства. Архивы не качаются: `fetch.py catalog` один раз читает их оглавления (пара мегабайт, `~/.avelune-sound/catalog/sonniss.json`), а `remotezip.py` вынимает из архива один файл по HTTP Range.
- **Freesound**: рейтинг 3,5+ от трёх и больше оценок, сначала самые скачиваемые, только CC0 и CC BY. Бесплатный ключ берётся на https://freesound.org/apiv2/apply (форма «Apply for API key»), потом `python "SETUP/sources.py" freesound-key КЛЮЧ --client-id CLIENT_ID`. Ключ хранится в `~/.avelune-sound/freesound.json`, в чат его не пиши. С ключом качается HQ-превью, после `sources.py freesound-login` (один раз подтвердить в браузере) качаются оригиналы WAV.
- **Kenney**: CC0-звуки интерфейса из зеркал на GitHub, по одному файлу. Сайт kenney.nl отдаёт паки только через одноразовую ссылку, поэтому файлы берутся с зеркал.

Каждый файл оценивается `real-sfx/scripts/quality.py` (A студийное, B хорошее, C превью и шипение, D клиппинг и пережатие). Оценка D удаляется сразу. Авторы и лицензии пишутся в `~/.avelune-sound/library/online/CREDITS.md`.

**Запасной путь: стартовая библиотека по ролям** (`starter_library.py`, без плана). Сначала Kenney, потом Freesound, потом Openverse. Openverse отдаёт с Freesound превью 128 кбит/с, это оценка C:
```
python "SETUP/starter_library.py" --dry
python "SETUP/starter_library.py" --register
python "SETUP/starter_library.py" --role foley --query "door creak" --register
```

**Оценка качества своих библиотек**: `python "RSFX/quality.py" --index` один раз проставит оценки всему индексу и покажет, сколько A/B/C/D в каждой библиотеке. Новые библиотеки `build_index.py` оценивает сам.

**Теги по смыслу** (поиск «найди глухой удар по дереву», 45 МБ, ставится в свою venv и систему не трогает):
```
python "RSFX/listen.py" install --yes
python "RSFX/listen.py" tag-index
```

## 3. earshot: «уши» агента (по желанию, ~1,1 ГБ моделей)

Без earshot озвучка работает, но выбор звука по смыслу и проверка «реальная запись или синтез» недоступны. Поставить:
```
# Windows: winget install astral-sh.uv   ·   macOS: brew install uv
uv tool install "earshot[mcp] @ git+https://github.com/Leonxlnx/earshot"
earshot doctor --fetch
claude mcp add earshot --scope user -e EARSHOT_THREADS=3 -- earshot mcp
```
На медленном компьютере запускай Claude Code с `MCP_TIMEOUT=60000`. Как пользоваться earshot, описано в скилле `earshot`.

## 4. Плагин не виден в Claude Code

- `claude plugin list` не показывает `avelune-sound`: обнови каталог (`claude plugin marketplace update avelune-labs`), затем `/plugin install avelune-sound@avelune-labs` и перезапусти Claude Code.
- Каталог взят из локальной папки: `claude plugin marketplace add "ПУТЬ/avelune-labs"`.
- После обновления плагина ничего настраивать заново не нужно: настройки лежат в `~/.avelune-sound`. Если на компьютере остался `config.json` внутри старой папки плагина, при первом запуске он сам скопируется в `~/.avelune-sound/real-sfx/`.

## 5. Самопроверка движка

```
python "${CLAUDE_SKILL_DIR}/../real-sfx/tests/selftest.py"     # ~2,5 мин, на своих тестовых звуках, данные пользователя не трогает
```
Норма: 187 из 188 проверок (проверка «the original under the new sounds is rebuilt without the synthesized clicks» падает и в исходном Real SFX).
