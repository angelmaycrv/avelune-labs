#!/usr/bin/env bash
# After an Agent/Task call returns, remind the coordinator that the result is unchecked.
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Avelune supervisor: агент вернул результат или был запущен. Результат ещё не сверен с брифом. Чек-лист приёмки: соответствие брифу, полнота, факты, формат, границы, согласованность с другими агентами, качество. При отклонении агент поправляется сообщением с конкретными пунктами."}}
JSON
