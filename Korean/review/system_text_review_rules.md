# DDON 한국어 패치 — 3단계: UI·업적·아이템·스킬·지명·폰 잡담 전수 검수 지침

You are reviewing (and where empty, translating) the Korean fan translation of Dragon's Dogma Online system text: achievements, item names/descriptions, skill/ability descriptions, spot/stage/enemy names, examine messages, mandragora info, UI labels/dialogs/system log, and untranslated pawn stage chatter.

## Input / output
- Input: `/tmp/claude-0/p3/batch_XX.json` — array of {id, gmd, jp, en, ko}. `gmd` = source file (context). `jp` = authoritative Japanese. `en` = community English (may be empty/loose). `ko` = current Korean (may be EMPTY = untranslated). `\r\n` = line break.
- Glossary: `/tmp/claude-0/p3/glossary.json` (Japanese term → Korean). Ability names (final, already decided — do NOT change them; use them when descriptions mention an ability): `/tmp/claude-0/p3/ability_names.json` (JP → KO).
- Output: `/tmp/claude-0/p3/out_XX.json` — ONLY changed/new entries: `{"id": <id>, "ko": "<Korean>", "why": "<category>"}`; why ∈ 번역(new translation of empty ko), 오역, 누락, 어순, 태그, 직역투, 용어, 말투, 맞춤법, 기타. Write with Python `json.dump(..., ensure_ascii=False)`.
- Use a private scratch folder `/tmp/claude-0/-home-claude/a06d1a83-34a9-5344-a20a-859f8ab0a916/scratchpad/p3_XX/` for helper scripts. Do not modify any other file.

## What to fix (only when clearly better — do not rewrite good lines for taste)
1. EMPTY ko → translate from the Japanese (why=번역). Remaining kana/kanji in ko → translate.
2. Mistranslation / meaning drift (오역), missing parts (누락), shifted/duplicated text (기타).
3. Broken word order, stranded particles, tag problems (어순/태그). After a tag use 에게, 에게서, 의, 에서, 에, (으)로, 을(를), 이(가), 은(는), 와(과) attached without a space.
4. Stiff literal Japanese-isms (직역투), wrong Korean spelling/spacing (맞춤법).
5. Terms vs glossary / settled decisions (용어).

## Category rules
- Names (item_name, spot_name, stage_list, enemy_name, achievement_name, skill names, job_emblem etc.): players already know these names from quests, so change a name ONLY for a clear error: leftover kana/kanji, wrong meaning, glossary conflict, misspelling, or obvious inconsistency inside the batch (same Japanese word rendered two ways — pick the majority/glossary form). Keep equipment series names consistent within the batch. Keep numbers, +N, Lv, ★, roman numerals, %, ASCII exactly.
- Descriptions (item_info, ability_info, skill info, achievement_info, efcSealedItemInfo, mandragora): plain written style ending "~한다/~된다/~할 수 있다" (or the noun-ending style the file already uses consistently). Damage/effect wording: "대미지", "~속성", "~에 대한 내성", "상태 이상". Ability names mentioned in 「」/【】 must match ability_names.json.
- Job names: ファイター=파이터, シーカー=시커, ハンター=헌터, プリースト=프리스트, シールドセージ=실드 세이지, ソーサラー=소서러, ウォリアー=워리어, エレメントアーチャー=엘리먼트 아처, アルケミスト=알케미스트, スピリットランサー=스피릿 랜서, ハイセプター=하이 셉터. Job damage strings use "파이터의 베기 속성 대미지 UP" style.
- UI labels/buttons/menu items: short noun phrases, no period; keep length close to the current Korean (screen space). Dialogs/system log: 합쇼체 "~합니다/~하시겠습니까?" consistently.
- Format specifiers and escapes must be preserved exactly and in the same order: %s %d %2.1f %%, {0}, \n literal text, etc.
- Pawn stage chatter (pawn\talk\stage\featureNNNN\personaNN.gmd): spoken by the player's pawn about the place. Persona voices (keep consistent): persona01 = 합쇼체/해요체 mix, earnest, calls player 각성자님; persona02 = 해요체, gentle, 각성자님; persona03 = 합쇼체, soldierly, 마스터; persona04 = 합쇼체, 주인님; persona05 = 해요체, 각성자님/당신; persona06 = 해요체, cheerful, 각성자님; persona07 = 합쇼체/해요체 polite, 각성자님; persona08 = 해요체, casual-polite. Follow the Japanese tone if a persona's line clearly differs. Max 34 chars per line; keep the Japanese line structure.
- Achievement names: noun phrases; achievement_info: "~한다" condition style ("~을(를) N회 달성한다" etc.) consistent within the file.

## Hard rules
- Every `<...>` tag preserved exactly (text and count). Keep 《》「」＜＞【】 brackets where the Japanese has them. Never write ASCII <...> around plain words.
- Line count: keep the current Korean's; if ko is empty or broken, use the Japanese line structure.
- No kana or kanji in output. Avoid rare Hangul syllables; prefer common words.
- Proper nouns: glossary / settled list / names used in the batch; never invent spellings.

## Process
Read the whole batch first. Then produce fixes. Before writing, verify with Python for every output entry: tag multiset equals the Japanese's; %-specifiers equal the Japanese's (when the current ko has them); line count equals the current Korean's or the Japanese's; no kana/kanji; only \r\n breaks. Fix failures.
Finish (under 80 words) with: total reviewed, total changed, counts per why, 3 examples, and cross-batch term questions.

## Project-wide decisions (apply)
- 禊の神殿 = 정화의 신전, エリアマスター = 지역 마스터, 依頼者 = 의뢰인, バートランド = 바트랜드, アルフレド = 알프레도, ネド = 네도, ベルタ = 베르타, 魔赤島 = 마적도, スポット = 스팟, マンドラゴラ = 만드라고라, 定型文 = 상용구, エモート = 감정 표현, 黒剣 = 흑검, 芯なる樹 = 중심 나무, 戦技 = 전투 기술.

## (phase-2 process, superseded below)
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

- Phase-3 additions: 戦徒の契り = 전우의 서약, 家財 = 가구(furniture items), レーゼ = 레제, 黄金石 = 황금석, マイ拠点 = 주 거점, 白衛騎士団 = 백위기사단, ガルドノック = 가르드노크, 闇炎 = 어둠의 불꽃, ドミニオン = 도미니언, 原始の雫 = 원초의 물방울, いいえ = 아니요, 戦徒 = 전우.
- Phase-3 settled (from batches 00–07): achievement job-level lines = "<직업> 직업 레벨 N 달성". エレメントアーチャー = 엘리먼트 아처 (never 엘리멘트), ハイセプター = 하이 셉터, アルケミスト = 알케미스트 (not 연금술사 as the job). メルガン = 메르간. バンデッド = 밴디드. エリアミッション = 지역 미션. 山麓 = 산기슭. 狂侵 = 광침. 淀みし大竜力 = 정체된 대용력. 〇〇の将 = 〇〇의 장수 (オークの将 = 오크 장수). Quest/enemy names inside achievement text: use the bracket the Japanese uses (《》「」【】), never ASCII [ ]. Keep Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ characters exactly as the Japanese has them (do not convert to ASCII I/II). Line breaks are always \r\n.
- Phase-3 settled (batches 08–17): attribute names — 斬 = 베기, 打 = 타격, 射 = 사격, 火/炎 = 화염, 氷 = 얼음, 雷 = 번개, 聖 = 성, 闇 = 어둠 ("베기 속성", "얼음 속성", "어둠 속성"; never 참/타/사/빙/뇌/암/빙결/뇌격). 聖防低下 = 성 속성 방어력 저하. クラフト用素材 = 제작 재료; material headers "X 계열 제작 재료" (爪牙系 = 발톱·이빨 계열). 吹き飛ばし力 = 넉백력. ステータス = 스테이터스. ギガン・マキナ = 기간 마키나. お風呂 = 욕조. スペリング = 스펠링. 魔矢 = 마시. Skill/ability names must match ability_names.json exactly (including spacing). Keep the source's line-break style for unchanged lines; changed lines use \r\n unless the whole file uses bare \n (then keep \n).
- Phase-3 settled (batches 18–27): slayer/crest names "X 계열 대미지＋N" (人型系 = 인간 계열, 腐死系 = 부패 계열, 骸骨系 = 해골 계열, 亜人系 = 아인 계열, 侵食系 = 침식 계열 …). The plus sign and spacing around numbers follow the Japanese exactly (＋ stays ＋, + stays +). 抗X = X 저항, 絶X = X 차단, 耐X = X 내성. "X 방어 저하" crests = "X 속성 방어력 저하". 理力 = 이력 (keep). ポーンの民 = 폰 일족. 属性異常/状態異常 = 상태 이상. 自室 = 개인실. パペット = 인형. 鱗砂 = 비늘 모래. サンダー = 선더. 遅 (status) = 둔화. 印記章 = 인장. Remove any leftover kanji such as 기(技) → 기.
- Phase-3 settled (batches 28–37): 曲者 = 무법자. 篭手/籠手 = 건틀릿. ワンズ = 완드. ハンズ = 핸즈. オーフリング = 올프링. パデット/バデット = 패딩. イェルハルド = 예르할트. 緋竜 = 홍룡 (飛竜 = 비룡). ヴァンクール = 방쿠르. 大盾 = 대형 방패. 胴 = 몸통. 【color/kanji】 suffix tags: keep the batch's existing majority rendering for each kanji; do not switch styles. 吹飛 in 【】 = 넉백. 火延焼 = 화염 연소. Equipment names from the English release (e.g. 디스웨이더) stay as they are.
- Phase-3 settled (batches 38–47): 手甲 = 완갑. 侵滅 = 침멸. 竜晶 = 용결정. 紫紺 = 자감. レッグス = 레그스. バレンタイン = 밸런타인. Variant separator ・ in item/furniture/recipe names = " - " (never leave the katakana ・; in sentences use ·). ピアス = 피어스 when part of an equipment series name already using it, else 귀걸이 — keep the batch majority. 解放 of a facility/job/feature = 해금; of a door/dungeon/area = 개방. 古の祭祀場 = 고대의 제사터. 湖畔の洞窟 = 호숫가 동굴. ウィルム = 웜, ワーム = 웜 (leave).
- Phase-3 settled (batches 48–57): 養根家 = 재배가. 樹内の記憶 = 나무 속의 기억. ベヘモット = 베헤모스. マンドラフレシア = 만드라 프레시아. マッシュルーム = 머쉬룸 (keep). 竜昌 = 용결정. 鬼 (enemy) = 오거, 小鬼 = 고블린. 里長 = 촌장. 抗侵薬 = 항침약. Mandragora colour/size suffixes use 【】 as the Japanese does. Leave dev placeholder lines (ハズレメッセージ etc.) unchanged.
- Phase-3 settled (batches 58–67): slayer families are always "X 계열" (人間系 = 인간 계열, 有翼系 = 유익 계열, 鬼人系 = 귀인 계열) — never 인간계/인간형. アルケム = 알케미 (アルケム・フーガ = 알케미 푸가). 溜め = 차지. マジックボール = 매직 볼. 遅延 = 지연. 聖吸 = 성흡, 闇霧 = 암무 (keep). 転身 = 전신. 助け起こし = 일으켜 세우기. 斬り崩し = 베어넘기기. えぐり突き = 후벼파기. エイド・モール/スラスト・モール = 에이드 몰/스러스트 몰. 魔物 = 마물. 燐光虫 = 인광충. セラー湖 = 세라 호수. Skill names: use the form in skill/normal_skill_name & custom_skill_name files (ability_names.json for abilities). Extra "코스트: N" lines that exist only in the Korean may stay (tags then match the current Korean).
- Phase-3 settled (batches 68–77): クリア = 클리어 (UI) / 완료 in sentences where natural — keep the file's majority. 精錬材 = 제련재. 軟体系 = 연체 계열. 呪詛系 = 저주 계열. 魔人斬り = 마인참. 黒呪の迷宮 = 흑주의 미궁. 魔印 = 마인. 戦甲 = 전갑. 魔球 = 마구. 大盾 in skill text may stay 대방패. Do not add or strip </KEYM> etc. on lines you don't otherwise change.
