---
name: sfx-toolkit
description: Связка трёх бесплатных инструментов для звука роликов и анимаций внутри Claude Code. Openverse ищет реальные записанные звуки с открытыми лицензиями, earshot «слушает» звук за агента (описание, совпадение с запросом, реальность, таймлайн, громкость, критика) и рендерит эффекты из кода, Real SFX и real-sound раскладывают реальные звуки по кадрам и сводят с музыкой и голосом. Установка, что когда использовать, общий конвейер от списка моментов до готового MP4 с отдельной дорожкой эффектов и файлом лицензий. Использовать, когда нужно озвучить видео, моушн, UI-анимацию, скринкаст или промо, а Claude не может слушать сам.
argument-hint: "[видео или проект, есть ли своя библиотека звуков, музыка и голос]"
---

# Набор SFX: Openverse + earshot + Real SFX

Ты звукорежиссёр монтажа, который работает в коде. Ты не слышишь, поэтому никогда не говоришь «звучит хорошо» без измерения, а каждый звук в итоговом ролике имеет источник и лицензию.

## Опора

- **Openverse** (openverse.org, проект WordPress, код MIT): поиск по ~5 млн аудио с открытыми лицензиями, без ключа. Скилл `avelune-sound:openverse`.
- **earshot** (Leon Lin, github.com/Leonxlnx/earshot, MIT, версия 0.4): «уши для агента». Локально на CPU описывает звук, оценивает совпадение с текстом, отличает реальную запись от синтеза, строит таймлайн фильма с синхронизацией к склейкам, меряет LUFS и true peak, критикует ролик по профилю 7 профессиональных лонч-фильмов; банк из 252 эффектов, отрендеренных кодом, и пресеты наборов звуков для фильма (например `calm` и `launch`). Модели CLAP и AudioSet-теггер (~1,1 ГБ) скачиваются один раз. Скиллы `avelune-sound:earshot` и `avelune-sound:real-sound` (из репозитория earshot).
- **Real SFX** (Clipwing, Александр Корбанов, github.com/Clipwing/skills, скрипты MIT): находит моменты в видео (по списку событий, проекту HyperFrames, скринкасту или картинке), подбирает реальные звуки из твоей библиотеки, ставит их на нужный кадр на правильном уровне, сохраняет музыку и голос, убирает вшитый синтез и отдаёт новый MP4, отдельный WAV эффектов, отчёт и самокритику. В комплекте 78 UI-звуков uisfx в 12 стилях (CC0). Скилл `avelune-sound:real-sfx`.
- Связку в один процесс описывает статья Gaurav Bisen «Claude Code Sound Effects: 3 Free Tools» (31.10.2026).

## Что когда брать

| Нужно | Инструмент |
|-------|-----------|
| Найти реальный звук, своей библиотеки нет или в ней нет нужного | Openverse (`scripts/openverse.py` в скилле `openverse`) |
| Выбрать лучший из кандидатов, проверить, что звук соответствует описанию | earshot `rank`, `match`, `describe` |
| Найти чистый кусок в длинной записи | earshot `find` |
| Проверить, не звучит ли ролик «синтетически» | earshot `realness` |
| Понять, что происходит в звуке ролика по секундам, синхронность со склейками | earshot `timeline`, `sheet` |
| Звук для кадра, которого нет ни в библиотеке, ни в Openverse | earshot `sfx render` (банк из 252) или `forge` (синтез с итерациями) |
| Разложить звуки по кадрам и свести с музыкой и голосом, есть своя библиотека | Real SFX (`real-sfx`) |
| Собрать полный саундтрек из лицензированных записей с музыкальным монтажом, мастерингом и титрами | real-sound (`real-sound`) |
| Громкость и пики итога | earshot `measure` (без моделей), нормы в `avelune-sound:mastering` |
| Оценка лонч-ролика | earshot `critique`, затем `avelune-sound:sound-review` |

Правило выбора: **реальная запись лучше синтеза**. Синтез earshot берётся, когда реального звука нет, и проверяется `realness` и прослушиванием человеком.

## Установка (один раз)

Нужны Python 3.10+, ffmpeg и ffprobe в PATH, для earshot ещё [uv](https://docs.astral.sh/uv/).

```bash
# Windows: winget install Python.Python.3.12; winget install Gyan.FFmpeg; winget install astral-sh.uv
# macOS: brew install ffmpeg-full uv  (обычный ffmpeg без drawtext и rubberband, нужных Real SFX)

# earshot: CLI и MCP-сервер
uv tool install "earshot[mcp] @ git+https://github.com/Leonxlnx/earshot"
earshot doctor --fetch                       # скачать две модели (~1,1 ГБ)
claude mcp add earshot --scope user -e EARSHOT_THREADS=3 -- earshot mcp   # модели остаются в памяти между вызовами

# Real SFX: библиотека и индекс. Запускать из папки скилла real-sfx внутри плагина.
# Чтобы настройки не стирались при обновлении плагина, храни конфиг отдельно:
#   REAL_SFX_CONFIG=~/.avelune-sound/real-sfx/config.json  (и абсолютный index_path в нём)
python scripts/setup.py scan "D:/Sounds"
python scripts/setup.py init --library main="D:/Sounds/SFX" --uisfx --index
python scripts/setup.py check

# Openverse: ничего ставить не нужно, только Python
python scripts/openverse.py search "whoosh" --commercial --category sound_effect --max-dur 3
```

Без своей библиотеки Real SFX работает только с UI-звуками uisfx; недостающие реальные звуки скачай через Openverse в папку и подключи её как библиотеку (`setup.py add-library openverse "D:/Sounds/openverse" --tier extra --index`). На медленном компьютере запускай Claude Code с `MCP_TIMEOUT=60000`.

## Общий конвейер

1. **Список моментов.** Если анимацию делал Claude, попроси список событий с временем кадра (`cues.json`). Иначе Real SFX найдёт моменты сам (`from_cues.py`, `ui_events.py`, `find_moments.py`) или earshot покажет таймлайн (`earshot timeline FILM.mp4`).
2. **Роли и стиль.** Для каждого момента роль (вжух, удар, поп, клик, клавиши, райзер, атмосфера) и правило из `avelune-sound:video-sound`: 3–6 акцентов на 15 секунд, тишина перед главным ударом.
3. **Источник звука по порядку:** своя библиотека → Openverse (`--commercial`, 3–5 кандидатов на роль, `get` с файлом лицензий) → банк earshot (`earshot sfx list --kind whoosh`, `earshot sfx render whoosh_fast/crisp -o whoosh.wav --dur 0.8`) → синтез `earshot forge`.
4. **Выбор ушами earshot:** `earshot rank` по описанию роли, `earshot realness` для финалистов. В отчёте всегда цифры (совпадение, p_real, LUFS), а не «звучит хорошо».
5. **Раскладка и микс:** Real SFX (`mix.py work/cues.json --out result/film_sfx.mp4 --plan`, потом без `--plan`; `--voice-safe`, если есть голос; `--duck`, если ролик держит музыка). Ориентиры: удар на кадре контакта, пик вжуха чуть после склейки (earshot `launch`: около +37 мс), клик около −11 мс от кадра.
6. **Проверка:** `critique.py` и `levels.py` из Real SFX, `earshot timeline --video` для синхронности, `earshot measure` для громкости (для соцсетей −14 LUFS и −1 dBTP), `earshot critique` для лонч-роликов.
7. **Человек слушает 5 моментов,** которые инструменты отметили как спорные, в наушниках и на динамике телефона. Real SFX умеет собрать страницу прослушивания (`listen_page.py`).
8. **Сдача:** MP4, отдельный WAV эффектов, отчёт по моментам, CREDITS.md из Openverse. Для звуков BY автор указывается в описании.

## Правила

- Не дублируй: если в рендере уже есть синтезированный звук, Real SFX заменяет его реальным, а не кладёт поверх.
- Не меняй проект и папки скиллов: рабочие файлы в `work/` и `result/`.
- Лицензии: Openverse по умолчанию только CC0, PDM, BY; свои библиотеки сохраняют свои лицензии; uisfx CC0; банк earshot рендерится кодом под MIT.
- Если инструмент не установлен, не притворяйся, что он сработал: скажи, что нужно поставить, и сделай ту часть, которая доступна.
