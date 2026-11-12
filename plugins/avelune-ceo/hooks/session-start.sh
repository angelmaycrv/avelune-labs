#!/usr/bin/env bash
# Context for the main agent at session start (plain stdout is added as context).
cat <<'TXT'
Avelune supervisor включён. Координатор отвечает за результат каждого агента, которого запускает: бриф с критериями приёмки перед запуском, проверка результата по брифу после, поправка агента сообщением при отклонении. Порядок описан в скилле avelune-ceo:supervisor.
TXT
