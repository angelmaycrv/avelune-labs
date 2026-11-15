# Сторонние компоненты

Плагин `avelune-sound` включает скиллы из сторонних открытых проектов без изменений. Их авторские права и лицензии сохраняются. Обновлять из источника: скопировать папку скилла заново и сверить этот файл.

| Скилл в плагине | Источник | Версия (коммит) | Лицензия |
|-----------------|----------|-----------------|----------|
| `skills/real-sfx` | [Clipwing/skills](https://github.com/Clipwing/skills/tree/main/skills/real-sfx), автор Alexander Korbanov (Clipwing) | `edbefcb` (21.10.2026) | Скрипты MIT (по README скилла, раздел «Licences»); uisfx: код MIT (Yuki Capital), звуки CC0 1.0 |
| `skills/earshot` | [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot/tree/main/skills/earshot), автор Leon Lin | `4ac3d2a` (06.11.2026, earshot 0.4.1) | MIT |
| `skills/real-sound` | [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot/tree/main/skills/real-sound), автор Leon Lin | `4ac3d2a` (06.11.2026) | MIT |

Openverse (openverse.org) используется через публичный API скриптом `skills/openverse/scripts/openverse.py`, написанным для этого плагина; код Openverse в плагин не входит. У каждого звука из Openverse своя лицензия, скрипт записывает её в CREDITS.md.

Модели earshot (CLAP `laion/larger_clap_general`, Apache-2.0; AST `MIT/ast-finetuned-audioset-10-10-0.4593`, BSD-3-Clause) в плагин не входят и скачиваются самим earshot при установке.

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
