# DDON 한국어 패치 — 퀘스트 정보 전수 검수 지침

You are reviewing an existing Korean fan translation of Dragon's Dogma Online quest information
(quest titles, objectives "다음 목적", quest summaries, board-quest descriptions).
The Korean came from machine translation with partial correction. Players report many problems.

## Input / output
- Input: `/tmp/claude-0/qa/qi_batch_XX.json` — array of {id, quest, key, jp, en, ko}.
  `jp` is the authoritative Japanese original. `en` is the community English translation (may be empty or loose). `ko` is the current Korean. `\r\n` is a line break.
- Glossary: `/tmp/claude-0/qa/glossary.json` (Japanese term → established Korean term). Use it for consistency.
- Output: `/tmp/claude-0/qa/qi_out_XX.json` — array with ONLY the entries you changed:
  `{"id": <id>, "ko": "<corrected Korean>", "why": "<category>"}`.
  `why` is one of: 오역, 누락, 어순, 태그, 직역투, 용어, 문체, 맞춤법, 기타.
  Write it with Python `json.dump(..., ensure_ascii=False)`.

## What to fix (change only when clearly better — do not rewrite good lines for taste)
1. Mistranslation / meaning drift vs the Japanese (오역), missing parts (누락).
2. Broken word order, particles stranded before tags, duplicated/moved tags (어순/태그).
3. Stiff literal Japanese-isms that a Korean player would find unnatural (직역투), e.g. Sino-Korean readings of Japanese words that are not Korean words (정형문→상용구 style problems), "~하는 것", unnatural passives.
4. Inconsistent terms vs the glossary or vs other entries of the same quest (용어).
5. Style consistency (문체):
   - Quest titles: noun phrase, no period.
   - Objectives (short one-liners, "다음 목적"): plain dictionary form ending: "~한다", "~에게 보고한다", "~(으)로 향한다", "~을(를) 쓰러뜨린다". No period.
   - Summaries / descriptions (multi-line): plain written narration "~한다/~했다/~해야 한다" unless the existing quest consistently uses another style; keep it consistent within a quest.
   - Board/request texts written by an NPC keep that NPC voice.
6. Spelling/spacing errors (맞춤법).

## Hard rules
- Every `<...>` tag must be preserved exactly (same text, same count). Keep 《》「」＜＞【】 brackets where the Japanese has them.
- After a tag (runtime name), use particle forms valid with or without a final consonant, attached without a space: 에게, 에게서, 의, 에서, 에, (으)로, 을(를), 이(가), 은(는), 와(과).
- Line count: normally keep the current Korean's. If the current Korean is broken (lines merged into one very long line, a particle pushed onto its own line, duplicated text, content shifted from another entry), use the Japanese line structure instead. Max 34 characters per line (raw tag text does not count).
- No kana or kanji in output. Avoid rare Hangul syllables (font has limited glyphs) — prefer common words.
- Proper nouns: keep the Korean names already used in the batch/glossary; do not invent new spellings.
- "（残り３）" style → "(남은 수: 3)".

## Process
Read the whole batch first (entries of the same quest give context). Then produce fixes.
Before writing, verify with Python for every output entry: tag multiset equals the Japanese's, line count equals either the current Korean's or the Japanese's, no kana/kanji, only \r\n line breaks. Fix failures.
Finish by replying with: total reviewed, total changed, counts per `why`, and 5 representative before→after examples.

## Project-wide decisions (already settled — apply them)
- 禊の神殿 = 정화의 신전. エリアマスター = 지역 마스터. 依頼者 = 의뢰인. 願いを聞き入れ = 부탁을 들어주고.
- バートランド = 바트랜드, アルフレド = 알프레도, ネド = 네도, ベルタ = 베르타, 魔赤島 = 마적도, スポット = 스팟.
- Delivery objective format: "＜<SQDI NAME>＞을(를) ＜<SQDI NUM>＞개 …에게 건넨다 (남은 수: <SQDI DNUM>)" — keep the brackets the Japanese uses.
- Remaining counters: "(남은 수: N)"; for places (残りNカ所) "(남은 곳: N)".
- Objectives never end in "~하기"; use "~한다". No trailing period on objectives/titles.
- Fake tags: never write ASCII <...> around plain Korean words; use ＜＞ instead.
