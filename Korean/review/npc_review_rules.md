# DDON 한국어 패치 — NPC·이벤트·폰·튜토리얼·기타 텍스트 전수 검수 지침

You are reviewing an existing Korean fan translation of Dragon's Dogma Online NPC everyday dialogue, event scenes, pawn chatter, tutorials, enemy titles, master/orb texts and other misc game text.
The Korean came from machine translation with partial correction; players report many problems.

## Input / output
- Input: `/tmp/claude-0/p2/batch_XX.json` — array of {id, file, speaker, jp, en, ko} (file = gmd file name, gives context). `jp` = authoritative Japanese. `en` = community English (may be empty/loose). `speaker` = English name of who speaks (use it to keep each character's voice consistent). `\r\n` = line break.
- Glossary: `/tmp/claude-0/p2/glossary.json` (Japanese term → established Korean term).
- Output: `/tmp/claude-0/p2/out_XX.json` — ONLY changed entries: `{"id": <id>, "ko": "<corrected Korean>", "why": "<category>"}`; why ∈ 오역, 누락, 어순, 태그, 직역투, 용어, 말투, 맞춤법, 기타. Write with Python `json.dump(..., ensure_ascii=False)`.

## What to fix (only when clearly better — do not rewrite good lines for taste)
1. Mistranslation / meaning drift vs Japanese (오역), missing parts (누락), text shifted from another line or duplicated (기타).
2. Broken word order, stranded particles, duplicated or moved tags (어순/태그).
3. Stiff literal Japanese-isms unnatural in Korean (직역투): e.g. "~하는 것이다" overuse, unnatural passives, Sino-Korean readings of Japanese words that aren't Korean words.
4. Character voice (말투): keep each speaker's speech level consistent across the batch — formal NPCs (knights, nobles, merchants to customers) use 합쇼체/하오체 as fits; rough characters 반말; pawns address the player politely as "마스터"/"각성자님" depending on the line. Fix sudden switches between 반말/존댓말 within one character unless the Japanese also switches.
5. Terms/names vs glossary (용어). 覚者 = 각성자, ポーン = 폰.
6. Spelling/spacing (맞춤법).

## Hard rules
- Every `<...>` tag preserved exactly (text and count). Keep 《》「」＜＞【】 brackets where the Japanese has them. Never write ASCII <...> around plain words.
- After a tag (runtime name) use particles valid with or without a final consonant, attached without space: 에게, 에게서, 의, 에서, 에, (으)로, 을(를), 이(가), 은(는), 와(과).
- Line count: keep the current Korean's; if the current Korean is broken (merged lines, particle alone on a line, duplicated/shifted text) use the Japanese line structure. Max 34 characters per line (raw tag text does not count).
- "――" (Japanese dash) may stay where it marks a trailing-off/pause, but do not add new ones; "…" is fine too. Keep consistent within a line.
- No kana or kanji in output. Avoid rare Hangul syllables; prefer common words.
- Proper nouns: use the glossary / names already used in the batch; never invent new spellings.

## Project-wide decisions (apply)
- 禊の神殿 = 정화의 신전, エリアマスター = 지역 마스터, 依頼者 = 의뢰인, バートランド = 바트랜드, アルフレド = 알프레도, ネド = 네도, ベルタ = 베르타, 魔赤島 = 마적도, スポット = 스팟, マンドラゴラ = 만드라고라, 定型文 = 상용구, エモート = 감정 표현, 黒剣 = 흑검, 芯なる樹 = 중심 나무, 戦技 = 전투 기술.

## Process
Read the whole batch first. Then produce fixes. Before writing, verify with Python for every output entry: tag multiset equals the Japanese's; line count equals the current Korean's or the Japanese's; no kana/kanji; only \r\n breaks. Fix failures.
Finish with: total reviewed, total changed, counts per why, 5 representative before→after examples, and any cross-batch term questions.

## Additional settled decisions (from earlier batches — apply)
- 竜力 = 용력, 悪しき竜 = 사악한 용, 礎 = 초석 (リムストーン = 림 스톤 is different), メガド = 메가도, 眠り狼亭 = 잠든 늑대 여관, 理 = 섭리, 釜戸 = 아궁이, 黒竜 = 흑룡, 離殿 = 별전, 商店区 = 상점가, ズール = 줄, ギルスタン = 길스턴, ゲルハルト = 예르할트, 火垂れ山 = 화수산, 護政区 = 호정구, 謁見の間 = 알현실.
- Speaker voices: Lise, Klaus, Mayleaf, Gillian, Loeg = 반말. Leo = 해라체. Joseph = 너/해라체 (おまえ). Alvar/Alfred toward the player = 하게체 / 귀공. Keep the player address word consistent per character.
- Do not mass-change sentence-final periods; leave punctuation style as is unless the line is otherwise edited.
- Use a private scratch folder named after your batch (e.g. scratchpad/qdXX/) for any helper scripts so you don't overwrite other agents' files.
- More settled: Sonel = 반말, calls the player 대장. 関所 = 관문. ジャン = 장. マルクス = 마르쿠스. 兵舎 = 병영. 家令 = 집사. 相棒 = 파트너. 集会所/集会場 = 집회소. 防衛区画 = 방어 구역. ポーン郷 = keep the existing "폰 대성당" (do not change). 瘴気 = 장기. グリッテン砦 = 그리텐 요새. 狩人の抜け穴 = 사냥꾼의 지름길. 青爪浜 = 청조 해변. Carrie (キャリー) = 반말 to player, calls player 너. Karen = 해요체.
- Ignore dev placeholder lines (受注時会話 etc.).
- More settled: メルゴダ = 메르고다, ウルテカ = 울테카, モルフォール = 모르포르, ディリス = 디리스, 晴天 = 맑은 날, 曇天 = 흐린 날, 酒場 = 주점, 将 (オークの将 etc.) = 장수, 白騎団 = 백기단, 賢者の古井戸 = 현자의 옛 우물. Fake English tags like <Fighter's Mark> → translate as ＜…＞ from the Japanese.
- More settled: ジョブマスター = 직업 마스터, ジョブ = 직업, 隠れ道 = 샛길 (王家の隠れ道 = 왕가의 샛길, 採掘師の隠れ道 = 채굴사의 샛길), 護符 = 부적, 呪印 = 저주 문양, エリアランク = 지역 랭크, シェリー = 셸리, 霊槍 = 영창(스피릿 랜스 무기명은 그대로), 王家の墓 = 왕가의 묘, 戦地 = 전장.
- Short UI-like strings (names, titles, labels) in this batch: noun phrases, no period; keep consistent with the glossary and with the same Japanese elsewhere in the batch.
- Pawn chatter files (pw/, pawn/, pw_talk/) are spoken by the player's pawn: polite toward the player ("마스터"/"각성자님") unless the Japanese persona is clearly casual; keep each persona file consistent.
- More settled: 兵舎 = 병영 (overrides glossary), 統率 = 통솔 (Leo's title "레오 통솔"), ガクシャ = 학자, 白翼覚者隊 = 백익단, ゴロツキ = 불량배, 黒き竜 = 검은 용 (黒竜 = 흑룡), 詰所 = 대기소, バジット = 바짓.
- More settled: 原始の雫 = 원초의 물방울, 侵食魔 = 침식마, キンガル = 킨갈, 覚者隊 = 각성자 부대, ルフロー = 루플로우, リム転移 = 림 텔레포트, 獣の将 = 짐승의 장수, いいえ = 아니요, リムの淵辺 = 림의 심연, 淀み = 정체, 大竜力 = 대용력, ヒュージ = 휴즈.
- More settled: 戦徒 = 전우 (NOT 전도), クラフトルーム = 제작실, グリンデュア = 그린듀어, 地鳴り = 땅울림, ベルトラン = 버트런드, ダクレイム砦 = 다크레임 요새, 森小人 = 숲 난쟁이.
- More settled: pawn persona04 = 합쇼체 (我が主/主 = 주인님), persona08 = 해요체. 自室 = 개인실. 転生 = 환생. 解放 (job/feature unlock) = 해금. Skip the repeated demo/placeholder lines (n5000–n8021 style) unchanged.
