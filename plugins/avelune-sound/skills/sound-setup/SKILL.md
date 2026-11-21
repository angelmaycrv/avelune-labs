---
name: sound-setup
description: "Установить и проверить звуковые инструменты avelune-sound: ffmpeg, библиотеку реальных звуков, earshot. Подключить свою папку со звуками, собрать стартовую библиотеку из Openverse. Использовать, когда просят настроить, починить или проверить звук-плагин, или doctor.py вернул не READY."
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

**Стартовая библиотека из Openverse** (нет своей или в ней не хватает ролей):
```
python "SETUP/starter_library.py" --dry                          # что будет скачано
python "SETUP/starter_library.py" --register                     # ~6 записей на роль, 11 ролей, CC0/PDM/BY
python "SETUP/starter_library.py" --register --tier extra        # если своя библиотека уже есть
python "SETUP/starter_library.py" --role foley --query "door creak" --register   # редкий звук
```
Скрипт пишет `catalog.csv` (тип каждого звука для подбора) и `CREDITS.md` (авторы и лицензии). Файлы из Freesound часто приходят как сжатое превью: для финального мастера бери оригинал по ссылке из `CREDITS.md`.

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
