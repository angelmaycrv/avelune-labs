# Сторонние компоненты

Плагин `avelune-sound` включает скиллы из сторонних открытых проектов. Их авторские права и лицензии сохраняются. Изменения перечислены ниже, в разделе «Что изменено в avelune-sound». Обновлять из источника: скопировать папку скилла заново, повторить изменения и сверить этот файл.

| Скилл в плагине | Источник | Версия (коммит) | Лицензия |
|-----------------|----------|-----------------|----------|
| `skills/real-sfx` | [Clipwing/skills](https://github.com/Clipwing/skills/tree/main/skills/real-sfx), автор Alexander Korbanov (Clipwing) | `edbefcb` (21.10.2026) | Скрипты MIT (по README скилла, раздел «Licences»); uisfx: код MIT (Yuki Capital), звуки CC0 1.0 |
| `skills/earshot` | [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot/tree/main/skills/earshot), автор Leon Lin | `4ac3d2a` (06.11.2026, earshot 0.4.1) | MIT |
| `avelune-sound-lab/skills/real-sound` (перенесён в плагин `avelune-sound-lab`) | [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot/tree/main/skills/real-sound), автор Leon Lin | `4ac3d2a` (06.11.2026) | MIT |

Openverse (openverse.org) используется через публичный API скриптом `skills/openverse/scripts/openverse.py`, написанным для этого плагина; код Openverse в плагин не входит. У каждого звука из Openverse своя лицензия, скрипт записывает её в CREDITS.md.

Модели earshot (CLAP `laion/larger_clap_general`, Apache-2.0; AST `MIT/ast-finetuned-audioset-10-10-0.4593`, BSD-3-Clause) в плагин не входят и скачиваются самим earshot при установке.

## Что изменено в avelune-sound (2.0.0)

- **real-sfx:** настройки и данные пользователя (config.json, индекс библиотеки, taste.json, стили, kind_map, кэши, venv и модели) хранятся в `~/.avelune-sound/real-sfx/` (переменная `REAL_SFX_HOME`), а не в папке скилла, потому что Claude Code заменяет папку плагина при каждом обновлении. Старый `config.json` из папки скилла копируется туда при первом запуске. Пустой `config.json` из поставки убран, `setup.py init --uisfx` не ставит uisfx заново, если он уже лежит в плагине. Описание скилла сокращено, в начало добавлена врезка о входе через `video-sound`. В `tests/selftest.py` добавлен `REAL_SFX_HOME` для временной папки. Остальной код без изменений.
- **earshot:** описание скилла сокращено и переведено, добавлена врезка: Loop 4 и Loop 5 (синтез) только по прямой просьбе пользователя; команда установки через `uv tool install`.
- Новые скрипты плагина (`sound-setup`, `sound-check`, `mix-master`, `sfx-design`, `ui-sounds`) написаны для avelune-sound, лицензия MIT.

## Real SFX: условия из README источника

> Scripts: MIT. uisfx (bundled mp3): code MIT, sounds CC0. Your own sound libraries keep their own licences; this skill never copies them anywhere, it only reads them.
>
> Made by Alexander Korbanov at Clipwing.

Отдельного файла LICENSE в репозитории Clipwing/skills на момент копирования не было; условия взяты из README скилла. Если Clipwing опубликует другие условия, они имеют приоритет.

## uisfx

MIT License

Copyright (c) 2026 Yuki Capital

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

### Звуки uisfx

The audio files under `sounds/` are dedicated to the public domain under the
Creative Commons CC0 1.0 Universal Public Domain Dedication.

You may copy, modify, distribute, and use these files, including commercially,
without asking permission. Attribution is appreciated but not required.

Legal code: https://creativecommons.org/publicdomain/zero/1.0/legalcode
SPDX identifier: CC0-1.0

## earshot

MIT License

Copyright (c) 2026 Leon Lin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
