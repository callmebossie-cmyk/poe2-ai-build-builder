# PoE2 AI Build Builder --- Project Plan

> เป้าหมาย: สร้าง Desktop Tool/EXE แบบ Path of Building Community
> ที่ให้ผู้ใช้เลือก **Main Skill + สไตล์การเล่น + งบ + เป้าหมายของ build** แล้ว AI
> วิเคราะห์แนวทางที่เป็นไปได้ ก่อนให้ผู้ใช้เลือกหนึ่งแนวทางและ Generate เป็น Full Build
>
> หลักสำคัญ: **โปรแกรมเป็นคนถือ Database / Graph / Calculator / Validator
> ส่วน AI เป็น Theorycrafter**\
> API key / AI cost เป็นของผู้ใช้แต่ละคนเอง

------------------------------------------------------------------------

## 1. Product Vision

ตัวอย่าง input:

-   Main Skill: `Snipe`
-   Goal: ใช้เป็น Main Skill จริง ไม่ใช่แค่ยิงบอส
-   Mapping: สำคัญ
-   Bossing: ปานกลาง--สูง
-   Gameplay: อยากให้ยิงไว ลดเวลารอ Perfect Timing
-   Budget: 5 Divine
-   League Start: ต้องการ / ไม่ต้องการ
-   Defense preference: optional

ผลลัพธ์รอบแรก:

1.  Fast Freeze Snipe
2.  Crit / Perfect Timing Snipe
3.  Cold Conversion Snipe
4.  Hybrid Clear + Snipe Boss

แต่ละทางต้องมี:

-   เหตุผลว่าทำไมเล่นได้
-   Class / Ascendancy ที่เหมาะ
-   Core mechanic
-   Difficulty
-   Budget
-   League-start viability
-   Mapping / Boss / Defense rating
-   จุดอ่อนและข้อแลกเปลี่ยน

เมื่อผู้ใช้กด `Pick Build` ระบบจึงวิเคราะห์รอบสองและสร้าง:

-   Class / Ascendancy
-   Passive Tree path
-   Main + Secondary skills
-   Support gems
-   Equipment bases
-   Unique items (ถ้าจำเป็น)
-   Affix priority
-   Defensive layers
-   Attributes / requirements
-   Mana/resource solution
-   Leveling progression
-   Endgame progression
-   Rotation
-   Upgrade priorities
-   Validation report
-   ในอนาคต: `.build` export

------------------------------------------------------------------------

# 2. ข้อค้นพบสำคัญเรื่องแหล่งข้อมูล

## 2.1 ไม่ควรใช้ PoE2DB เป็น Database หลักตั้งแต่แรก

PoE2DB เหมาะกับ:

-   ตรวจสอบข้อมูลด้วยคน
-   cross-check mechanic
-   reference หน้า skill/item
-   ใช้ตรวจความถูกต้องระหว่าง development

แต่ไม่ควรวาง architecture ให้โปรแกรมต้อง scrape PoE2DB ทุกครั้ง

เหตุผล:

1.  มี community export ที่เป็น structured data อยู่แล้ว
2.  Passive Tree มี official export จาก GGG แล้ว
3.  PoE2DB ไม่ได้มี public data API ที่ชัดเจนสำหรับงานนี้
4.  การเอาข้อมูลเว็บอื่นมา redistribute ต้องพิจารณา permission/license เพิ่ม

**ข้อเสนอ:** ใช้ GGG + RePoE + PoB2 เป็นแหล่งหลัก แล้วใช้ PoE2DB เป็น
reference/fallback

------------------------------------------------------------------------

# 3. Data Sources ที่แนะนำ

## Source A --- GGG Official PoE2 Passive Skill Tree Export

**แหล่ง:** Grinding Gear Games

Repository:

`https://github.com/grindinggear/poe2-skilltree-export`

มี:

-   Passive nodes
-   Node IDs
-   Stats ของ node
-   Tree groups
-   Connections
-   Positions
-   Class starting positions / tree structure
-   Assets ที่เกี่ยวข้องกับ passive tree

ไฟล์หลัก:

`data.json`

### วิธีเอามา

ช่วง development:

``` bash
git clone https://github.com/grindinggear/poe2-skilltree-export.git
```

หรือ downloader ของโปรแกรมสามารถ download release/data.json ตาม version
ที่รองรับ

จากนั้น importer ของเราทำ:

``` text
GGG data.json
      ↓
parse
      ↓
normalize
      ↓
SQLite
      ↓
passive_nodes
passive_edges
passive_groups
class_starts
```

### สถานะ

**ควรถือเป็น authoritative source สำหรับ Passive Tree**

หมายเหตุ: เอกสาร Developer ของ GGG เคยระบุว่า PoE2-specific data exports
ยังไม่มี แต่ GGG ได้เปิด repository `poe2-skilltree-export` แยกออกมาแล้วในปี
2026 ดังนั้น implementation ต้องอิง repository ปัจจุบันสำหรับ tree และอย่าคาดว่า
official export จะครอบคลุม gems/items/mods ทั้งหมด

------------------------------------------------------------------------

# 4. RePoE Fork --- แหล่ง structured game data หลัก

Organization:

`https://github.com/repoe-fork`

PoE2 export:

`https://github.com/repoe-fork/poe2`

Exporter:

`https://github.com/repoe-fork/repoe`

RePoE เป็น community tooling ที่ extract ข้อมูลจาก game files แล้วแปลงออกมาเป็น
JSON

ข้อมูลที่ ecosystem นี้รองรับ/มีประโยชน์กับเรา เช่น:

-   stats
-   mods
-   base items
-   gems
-   active skill types
-   characters
-   cost types
-   item classes
-   monster stats
-   crafting-related data
-   และข้อมูลจาก `.dat` อื่น ๆ ที่ exporter รองรับ

### Data pipeline

``` text
PoE2 Game Files
     ↓
.dat / bundle data
     ↓
PyPoE + schema
     ↓
RePoE exporter
     ↓
JSON
     ↓
Our importer
     ↓
poe2.db
```

### วิธีใช้ใน Phase แรก

**ไม่ต้องเขียน extractor เองก่อน**

ใช้ hosted/exported JSON ของ `repoe-fork/poe2` แล้วเขียน importer
ของเราให้แปลง schema ของ RePoE → internal schema

ตัวอย่าง:

``` text
RePoE gems
     ↓
skills
supports
skill_tags
skill_levels

RePoE base items
     ↓
item_bases

RePoE mods
     ↓
mods
mod_spawn_rules
mod_tags
```

### Phase หลัง

ถ้าต้องการ independence มากขึ้น:

-   install local PoE2
-   ใช้ exporter tooling
-   extract จาก game data
-   generate JSON ของเราเองใน build/update pipeline

**อย่าเริ่มจากการ reverse-engineer ทุกอย่างเองใน MVP**

------------------------------------------------------------------------

# 5. Path of Building Community --- PoE2

Repository:

`https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2`

นี่เป็น reference ที่สำคัญมากที่สุดอีกตัวหนึ่ง เพราะ PoB2 ทำสิ่งที่ใกล้กับ engine
ที่เราต้องการอยู่แล้ว

PoB2 มี:

-   Passive Tree planner
-   Skill planner
-   Support interactions
-   Item planner
-   Unique database
-   Modifier parsing
-   Offence calculation
-   Defence calculation
-   Item crafting logic
-   Build import/export
-   Generated game data
-   Export scripts

PoB documentation ระบุว่าไฟล์จำนวนมากใน `src/Data` ถูก generate จาก Path of
Exile game data ผ่าน scripts ใน `src/Export`

ดังนั้น PoB ไม่ได้ "เรียก API เว็บเพื่อถามทุกอย่างตอนเปิดโปรแกรม"

แนวคิดหลักคือ:

``` text
Game data
    ↓
Exporter
    ↓
Generated local data
    ↓
PoB calculation engine
```

ซึ่งเป็น architecture เดียวกับที่ PoE2 AI Builder ควรใช้

------------------------------------------------------------------------

# 6. PoB Data Export / Community Data

RePoE fork ecosystem ยังมี:

`https://github.com/repoe-fork/pob-data`

ข้อมูลบางประเภทใน PoB ไม่ได้มาจาก game files แบบตรง ๆ

ตัวอย่างสำคัญคือข้อมูล Unique บางส่วนที่ PoB team maintain เอง

ดังนั้น source priority ควรเป็น:

``` text
Official GGG
   ↓
Extracted Game Data (RePoE)
   ↓
PoB Community Data
   ↓
PoE2DB / Wiki reference
```

ไม่ใช่:

``` text
scrape PoE2DB ทั้งเว็บ
```

------------------------------------------------------------------------

# 7. PoE2DB ใช้ตรงไหน

PoE2DB:

`https://poe2db.tw/`

ใช้เป็น:

### Human verification source

เช่น developer เปิดตรวจ:

-   Snipe level scaling
-   skill tags
-   support compatibility
-   unique text
-   mechanic wording
-   patch change

### Fallback research

ถ้า structured export ไม่มี field ที่ต้องการ อาจตรวจว่า PoE2DB มีข้อมูลหรือไม่

แต่ก่อนทำ automated scraping / caching / redistribution:

**ต้องตรวจ Terms/permission หรือขออนุญาตเจ้าของ PoE2DB**

ดังนั้น MVP **ไม่ควร dependency กับ PoE2DB scraper**

------------------------------------------------------------------------

# 8. Official Path of Exile API ใช้ทำอะไร

GGG Developer Docs:

`https://www.pathofexile.com/developer/docs`

Official API ใช้กับข้อมูล server/account/live service มากกว่าการเป็น static
game database

ตัวอย่าง resources ปัจจุบันมี:

-   Account Profile
-   Account Characters
-   Leagues
-   Currency Exchange
-   OAuth
-   และ endpoints อื่นตาม API Reference

### สิ่งที่ Official API เหมาะกับ Tool นี้

อนาคต:

``` text
Login with Path of Exile
        ↓
OAuth
        ↓
Character
        ↓
Current equipment
Current gems
Current character state
        ↓
AI Analyze My Character
```

หรือ:

``` text
Currency Exchange
      ↓
economy information
```

### สิ่งที่ไม่ควรคาดหวังจาก API

อย่าคาดว่า endpoint เดียวจะให้:

``` text
ALL SKILLS
ALL SUPPORTS
ALL MODS
ALL BASE ITEMS
ALL PASSIVES
ALL GAME MECHANICS
```

static game data ส่วนใหญ่ยังต้องมาจาก official export / game-data extraction
/ community datasets

------------------------------------------------------------------------

# 9. Data Source Matrix

  -----------------------------------------------------------------------------
  Data                Primary Source            Secondary       Local?
  ------------------- ------------------------- --------------- ---------------
  Passive Tree        GGG                       PoB2            Yes
                      `poe2-skilltree-export`                   

  Passive connections GGG tree export           PoB2            Yes

  Ascendancy nodes    GGG tree / extracted data PoB2            Yes

  Skill Gems          RePoE PoE2                PoB2            Yes

  Support Gems        RePoE PoE2                PoB2            Yes

  Skill level scaling RePoE / game extraction   PoB2            Yes

  Base Items          RePoE PoE2                PoB2            Yes

  Item Mods           RePoE PoE2                PoB2            Yes

  Mod spawn rules     RePoE PoE2                PoB2            Yes

  Unique Items        PoB2 + extracted data     PoE2DB          Yes
                                                verification    

  Character constants RePoE / PoB2              ---             Yes

  Monster constants   RePoE / PoB2              ---             Yes

  Calculation logic   Our engine + PoB2         ---             Code
                      reference                                 

  Character/account   GGG API + OAuth           ---             Live

  League info         GGG API                   community       Live/cache

  Currency exchange   GGG API                   ---             Live/cache

  Market item prices  Later provider            trade/economy   Live
                                                source          

  Mechanics           curated layer             PoE2DB / Wiki   Local curated
  explanations                                                  
  -----------------------------------------------------------------------------

------------------------------------------------------------------------

# 10. Internal Database

ใช้ SQLite:

``` text
data/
└── poe2.db
```

schema เริ่มต้น:

``` text
game_versions

skills
skill_levels
skill_tags
skill_stats

support_gems
support_tags
support_compatibility

passive_nodes
passive_edges
passive_groups
passive_stats

ascendancies
ascendancy_nodes

item_bases
item_classes

mods
mod_stats
mod_tags
mod_spawn_rules

unique_items
unique_mods

characters
game_constants
monster_constants

mechanics
mechanic_relations

data_sources
data_versions
```

ทุก record สำคัญควรมี:

``` text
source
source_version
game_patch
imported_at
```

เพื่อ debug ได้ว่า data มาจากไหน

------------------------------------------------------------------------

# 11. Data Update System

ไม่ฝัง DB ถาวรเป็นส่วนเดียวกับ EXE

โครงสร้าง:

``` text
PoEAIBuilder/
├── PoEAIBuilder.exe
├── data/
│   ├── poe2.db
│   └── manifest.json
├── config/
├── cache/
└── logs/
```

manifest:

``` json
{
  "game": "poe2",
  "patch": "x.x.x",
  "database_version": 1,
  "sources": {
    "passive_tree": "GGG",
    "gems": "RePoE",
    "items": "RePoE",
    "calculation_reference": "PoB2"
  }
}
```

เมื่อ patch ใหม่:

``` text
Check Data Update
      ↓
download new source snapshots
      ↓
build temporary DB
      ↓
validate
      ↓
swap database
```

ไม่ต้องออก EXE ใหม่เพียงเพราะ skill damage เปลี่ยน

------------------------------------------------------------------------

# 12. Context Builder --- ห้ามโยน Database ทั้งเกมเข้า AI

User:

``` text
Snipe
Fast
Mapping
5 Div
League Start
```

โปรแกรมทำ deterministic retrieval ก่อน:

``` text
Snipe
 ↓
tags
 ↓
mechanics
 ↓
compatible supports
 ↓
relevant passives
 ↓
relevant ascendancies
 ↓
relevant item mods
 ↓
relevant uniques
```

แล้วสร้าง `BuildContext`:

``` json
{
  "main_skill": {},
  "mechanics": [],
  "supports": [],
  "passive_candidates": [],
  "ascendancy_candidates": [],
  "item_candidates": [],
  "constraints": {}
}
```

AI เห็นเฉพาะ candidate set

------------------------------------------------------------------------

# 13. AI Pipeline

## Round 1 --- Build Direction

Input:

``` text
Main Skill
Playstyle
Budget
Mapping/Boss preference
League Start
Defense preference
Relevant game data
```

Output structured JSON:

``` text
3–5 Build Directions
```

AI ต้องอธิบาย:

-   concept
-   synergy
-   class
-   ascendancy
-   expected difficulty
-   budget
-   strengths
-   weaknesses

------------------------------------------------------------------------

## Round 2 --- Full Build

หลัง user เลือก:

``` text
Selected direction
      ↓
retrieve deeper data
      ↓
AI theorycraft
      ↓
candidate build
```

------------------------------------------------------------------------

# 14. Validator

AI ห้ามเป็น source of truth เรื่อง graph/math

Validator ตรวจ:

### Passive

``` text
node exists?
connected?
valid class start?
point count?
ascendancy requirements?
```

### Gems

``` text
gem exists?
support compatible?
requirements valid?
weapon requirement?
```

### Equipment

``` text
base exists?
mod can spawn?
prefix/suffix count?
item level requirement?
```

### Character

``` text
attributes sufficient?
resistance?
resource?
defensive layers?
```

ถ้า fail:

``` text
Validator
   ↓
error report
   ↓
AI revise
   ↓
validate again
```

------------------------------------------------------------------------

# 15. Calculation Engine

นี่เป็น Phase ใหญ่แยกต่างหาก

เป้าหมายระยะยาว:

``` text
Build
 ↓
Calculate
 ↓
Hit Damage
DPS
Attack/Cast Rate
Crit
Ailments
Effective HP
Armour
Evasion
ES
Mana/resource sustainability
```

PoB2 เป็น reference implementation ที่ควรศึกษาอย่างจริงจัง แทนการให้ LLM
คำนวณสูตรเอง

**MVP ไม่จำเป็นต้อง clone calculation engine ของ PoB ทั้งหมดทันที**

เริ่มจาก:

1.  structural validation
2.  simple stat aggregation
3.  core damage calculation สำหรับ skill ที่ทดสอบ
4.  ค่อยขยาย mechanics

------------------------------------------------------------------------

# 16. AI Provider Architecture

``` text
AIProvider
│
├── OpenAI
├── Anthropic
├── Google
└── Local (future)
```

User เป็นคนใส่ credential ของตัวเอง

``` text
Settings
→ AI Provider
→ API Key
→ Model
→ Reasoning Level
```

เก็บ API key ใน secure OS credential storage

**ห้ามเก็บ key เป็น plaintext ใน config.json**

------------------------------------------------------------------------

# 17. Desktop Stack

แนะนำ:

``` text
Frontend
React + TypeScript

Desktop
Tauri

Backend/Core
Rust หรือ TypeScript ในช่วง prototype

Database
SQLite

AI
Provider abstraction

Updater
Tauri updater + separate data updater
```

เหตุผลที่เลือก Tauri:

-   ทำ Windows EXE ได้
-   app เบากว่า Electron โดยทั่วไป
-   local SQLite ได้
-   secure credential integration ทำได้
-   frontend ทำ UI แบบ web ได้ง่าย

ถ้าต้องการ prototype เร็วที่สุด Electron ก็ใช้ได้ แต่ final community app แนะนำ
Tauri

------------------------------------------------------------------------

# 18. Development Phases

## Phase 0 --- Legal / Data Audit

-   [ ] ตรวจ license GGG developer policy
-   [ ] ตรวจ license PoB2
-   [ ] ตรวจ license RePoE tooling
-   [ ] แยก code license กับ game data
-   [ ] ไม่ใช้ PoE2DB redistribution จนกว่าจะชัดเจนเรื่อง permission

------------------------------------------------------------------------

## Phase 1 --- Data Proof of Concept

เป้าหมาย: ยังไม่ต้องมี AI

-   [ ] download GGG PoE2 passive tree
-   [ ] download RePoE PoE2 exports
-   [ ] inspect PoB2 data
-   [ ] design SQLite schema
-   [ ] importer
-   [ ] import Snipe
-   [ ] import related supports
-   [ ] import passive tree
-   [ ] import ascendancy
-   [ ] import item bases/mods

Test:

``` text
search Snipe
→ show skill data

search Projectile passives
→ show nodes

path A → B
→ shortest path
```

------------------------------------------------------------------------

## Phase 2 --- Snipe Vertical Slice

ทำแค่ **Snipe** ให้ครบก่อน

-   [ ] User selects Snipe
-   [ ] User chooses playstyle
-   [ ] candidate retrieval
-   [ ] AI generates 3 build directions
-   [ ] Pick one
-   [ ] AI generates basic build
-   [ ] validator checks it

ถ้า Snipe vertical slice ใช้งานจริงได้ แสดงว่า architecture ผ่าน

------------------------------------------------------------------------

## Phase 3 --- Generic Skill Engine

เอา hard-code ของ Snipe ออก

``` text
ANY SKILL
   ↓
tags/mechanics
   ↓
candidate retrieval
   ↓
AI
```

------------------------------------------------------------------------

## Phase 4 --- Calculation

-   [ ] stat aggregation
-   [ ] damage
-   [ ] defense
-   [ ] resource
-   [ ] ailments
-   [ ] compare alternatives

------------------------------------------------------------------------

## Phase 5 --- PoE Account Integration

ใช้ GGG OAuth/API

-   [ ] register application
-   [ ] OAuth
-   [ ] import character
-   [ ] analyze current character
-   [ ] "Improve My Build"

------------------------------------------------------------------------

## Phase 6 --- Community Release

-   [ ] installer
-   [ ] auto updater
-   [ ] data updater
-   [ ] API key setup
-   [ ] provider selection
-   [ ] crash/log system
-   [ ] source attribution
-   [ ] GGG non-affiliation notice
-   [ ] license audit
-   [ ] GitHub releases

------------------------------------------------------------------------

# 19. สิ่งที่ควรทำเป็นอันดับแรกจริง ๆ

อย่าเริ่มจาก UI

อย่าเริ่มจาก Astra

อย่าเริ่มจาก scrape PoE2DB

เริ่มจาก:

``` text
STEP 1
GGG Passive Tree
       +
RePoE PoE2
       +
PoB2
       ↓
ตรวจว่าเราได้ข้อมูลอะไรครบแล้วบ้าง
```

จากนั้น:

``` text
STEP 2
สร้าง Data Source Inventory
```

ตัวอย่าง:

``` text
Snipe
✓ name
✓ tags
✓ level stats
✓ requirements
✓ skill types
? exact mechanic annotations

Passive
✓ nodes
✓ stats
✓ connections
✓ positions

Items
✓ bases
✓ mods
? unique interpreted effects
```

แล้วค่อยเติมช่องว่าง

------------------------------------------------------------------------

# 20. Source Priority Rule

ใช้ rule นี้ตลอดโปรเจกต์:

``` text
1. GGG Official
       ↓
2. Extracted game data
       ↓
3. Path of Building Community
       ↓
4. Other established community datasets
       ↓
5. PoE2DB / Wiki verification
       ↓
6. Manual curated data
```

และเก็บ provenance ทุกครั้ง

------------------------------------------------------------------------

# 21. ข้อสรุปเรื่อง "เมื่อก่อนเว็บ PoE ดึง API มาจากไหน"

มีโอกาสสูงที่เว็บ/tool ที่ดูเหมือน "ดึง API ข้อมูล PoE" จะใช้คนละแหล่งตามประเภทข้อมูล
ไม่ได้มี official API เดียวที่เป็นฐานข้อมูลเกมทั้งหมด

ภาพจริงของ ecosystem คือ:

``` text
GGG Official API
→ account / league / server resources / exchange ฯลฯ

GGG Official Data Export
→ passive tree (รวม PoE2 tree export ที่มีแล้ว)

Game Files
→ gems / mods / bases / constants / internal data

PyPoE / RePoE
→ extract + convert game data เป็น structured JSON

Path of Building
→ game data + generated data + hand-maintained logic/data
→ calculation engine

PoE2DB
→ community database/reference
```

ดังนั้นสำหรับ **PoE2 AI Builder** เราไม่จำเป็นต้องพึ่ง PoE2DB เป็นฐานหลักเลย

------------------------------------------------------------------------

# 22. MVP Definition

MVP ถือว่าสำเร็จเมื่อ:

``` text
User:
"Snipe / Fast / Mapping / Cheap"

↓ program retrieves real game data

AI:
เสนออย่างน้อย 3 viable approaches

↓ user picks one

AI:
สร้าง class + ascendancy + gems + supports
+ passive direction + gear priorities

↓ validator

Program:
ยืนยันว่า nodes/gems/items ที่อ้างถึงมีอยู่จริง
และ passive path เดินได้จริง
```

**ยังไม่ต้องแม่น DPS ระดับ PoB ใน MVP**

เมื่อ loop นี้ทำงานได้ ค่อยเพิ่ม calculation engine

------------------------------------------------------------------------

# 23. Next Immediate Task

สร้าง repository:

``` text
poe2-ai-builder/
├── app/
├── core/
├── data/
├── importer/
│   ├── ggg-tree/
│   ├── repoe/
│   └── pob/
├── ai/
├── validator/
├── calculator/
├── docs/
└── tests/
```

งานแรกของ `importer/`:

1.  `fetch_ggg_tree`
2.  `fetch_repoe_poe2`
3.  `inspect_pob2`
4.  `normalize`
5.  `build_sqlite`
6.  `generate_manifest`
7.  `validate_database`

หลังจากนั้นจึงเริ่ม **Snipe Vertical Slice**

------------------------------------------------------------------------

## Reference URLs

-   GGG Developer Docs: https://www.pathofexile.com/developer/docs
-   GGG Data Exports: https://www.pathofexile.com/developer/docs/data
-   GGG PoE2 Passive Tree Export:
    https://github.com/grindinggear/poe2-skilltree-export
-   RePoE Fork organization: https://github.com/repoe-fork
-   RePoE exporter: https://github.com/repoe-fork/repoe
-   RePoE PoE2 export: https://github.com/repoe-fork/poe2
-   RePoE PoB export: https://github.com/repoe-fork/pob-data
-   Path of Building Community PoE2:
    https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2
-   PoE2DB: https://poe2db.tw/

------------------------------------------------------------------------

## Final Architecture Principle

> **Database tells us what exists.**\
> **Graph tells us where we can go.**\
> **Calculator tells us what the numbers are.**\
> **Validator tells us whether the build is legal.**\
> **AI decides which combination best satisfies what the player actually
> wants.**

------------------------------------------------------------------------

# 24. Instructions for the AI Coding Agent

ส่วนนี้เป็นคำสั่งสำหรับ AI/Coding Agent ที่ได้รับไฟล์นี้ไปสร้างโปรแกรมต่อ

## Mission

อ่านเอกสารนี้ทั้งหมดและ **เริ่มสร้างโปรเจกต์จริงตามแผนทันที** ไม่ใช่เพียงสรุป วิเคราะห์
หรือเสนอ architecture เพิ่ม

ให้ทำงานแบบ autonomous/agentic ให้มากที่สุด:

> **Implement the entire plan autonomously, but execute it
> phase-by-phase. Do not stop after planning.**

AI ต้องทำสิ่งที่สามารถทำเองได้ทั้งหมด เช่น:

-   สร้าง repository/project structure
-   clone/download public repositories และ datasets ที่จำเป็น
-   อ่าน official documentation
-   inspect source/schema
-   ติดตั้ง dependencies ผ่าน command line เมื่อปลอดภัยและเหมาะสม
-   เขียน importer
-   สร้าง SQLite database
-   เขียน graph/pathfinding
-   เขียน validator
-   เขียน tests
-   run tests
-   debug
-   สร้าง AI provider abstraction
-   สร้าง UI
-   build desktop application
-   build Windows EXE/installer เมื่อถึง phase นั้น
-   สร้าง/update README, TODO และ development notes
-   ตรวจสอบความคืบหน้ากับ acceptance criteria ของแต่ละ checkpoint

**อย่าถาม User ในสิ่งที่ AI สามารถตรวจสอบ ค้นหา ตัดสินใจ หรือทำเองได้จาก
repository, documentation, source code, terminal หรือ test results**

------------------------------------------------------------------------

# 25. User Intervention Protocol

เมื่อมีขั้นตอนที่ AI ทำเองไม่ได้จริง ๆ และจำเป็นต้องให้ User ลงมือ เช่น:

-   สมัคร/register API application
-   Login account
-   OAuth approval
-   สร้างหรือคัดลอก API key
-   ยืนยัน permission
-   ขอ permission/license จาก data provider
-   กด OS security/administrator dialog ที่ agent เข้าถึงไม่ได้
-   ติดตั้ง/เปิดโปรแกรมผ่าน GUI ที่ agent ไม่สามารถควบคุมได้
-   การตัดสินใจที่มีผลต่อค่าใช้จ่ายจริง
-   การยอมรับ Terms/License ในนาม User
-   secret/credential ที่ User ต้องเป็นผู้จัดหา

ให้หยุด **เฉพาะงานที่ blocked** และบอก User อย่างชัดเจนว่า:

1.  ต้องทำอะไร
2.  ต้องไปที่ไหน
3.  ต้องกด/กรอกอะไร
4.  ทำเสร็จแล้วต้องส่งอะไรกลับมาให้ AI
5.  งานส่วนไหนกำลังถูก block
6.  มีงานอื่นที่ AI สามารถทำต่อระหว่างรอได้หรือไม่

หากมีงานอื่นที่ไม่ถูก block ให้ AI ทำงานเหล่านั้นต่อได้เลยแทนที่จะหยุดทั้งโปรเจกต์

------------------------------------------------------------------------

# 26. USER_ACTION_REQUIRED.md

ให้สร้างไฟล์นี้ไว้ที่ root ของ repository:

``` text
USER_ACTION_REQUIRED.md
```

ใช้เป็นรายการสิ่งที่ต้องการการกระทำจาก User

ตัวอย่าง:

``` markdown
# USER ACTION REQUIRED

## GGG OAuth Registration
Status: BLOCKED

Why:
OAuth Client ID ต้องถูกสร้างโดยเจ้าของ account

Steps:
1. Open the GGG developer page.
2. Sign in.
3. Register the application using the values listed below.
4. Copy the Client ID.
5. Add it to the specified local configuration/secret store.

Return to the agent with:
"GGG OAuth complete"

Do NOT paste secrets into source control.
```

เมื่อ User ทำเสร็จแล้ว:

-   mark task เป็น `COMPLETE`
-   ทำงานต่อจาก checkpoint เดิม
-   ห้ามเริ่มโปรเจกต์ใหม่หรือทำสิ่งเดิมซ้ำโดยไม่จำเป็น

------------------------------------------------------------------------

# 27. Project State Management

AI ต้องรักษาสถานะของโปรเจกต์ระหว่างการทำงาน

สร้างอย่างน้อย:

``` text
README.md
TODO.md
USER_ACTION_REQUIRED.md
docs/DEVELOPMENT_STATUS.md
```

`DEVELOPMENT_STATUS.md` ควรบันทึก:

-   Current Phase
-   Current Checkpoint
-   Completed work
-   Tests passing/failing
-   Known issues
-   Current blockers
-   Data versions
-   Important architectural decisions
-   Next task

ก่อนเริ่ม session ใหม่หรือหลัง context ถูกย่อ ให้ AI อ่านไฟล์สถานะเหล่านี้ก่อนทำงานต่อ

------------------------------------------------------------------------

# 28. Implementation Order --- Mandatory

**ห้ามเริ่มจาก UI เป็นหลัก**

**ห้ามใช้ mock data เพื่อทำให้โปรแกรมดูเหมือนทำงานได้ แล้วถือว่า checkpoint ผ่าน**

**ห้ามเริ่มจากการ scrape PoE2DB**

ให้ดำเนินงานตามลำดับนี้:

``` text
REAL DATA
   ↓
NORMALIZATION
   ↓
LOCAL DATABASE
   ↓
PASSIVE GRAPH
   ↓
RETRIEVAL
   ↓
AI THEORYCRAFTING
   ↓
VALIDATION
   ↓
CALCULATION
   ↓
DESKTOP UI
   ↓
EXE / INSTALLER
```

UI prototype เล็ก ๆ ทำได้ถ้าจำเป็นต่อการทดสอบ แต่ห้ามให้ UI development แซง core
data/engine work

------------------------------------------------------------------------

# 29. Mandatory Checkpoints

## Checkpoint 1 --- Real Data Import

ต้องพิสูจน์ว่า Snipe และข้อมูลที่เกี่ยวข้องถูก import จาก **แหล่งข้อมูลจริง** เข้า local
database ได้

Acceptance:

``` text
Snipe exists in database
Skill tags available
Level/stat data available
Related support data queryable
Passive data available
Ascendancy data available
Relevant item/mod data queryable
Data provenance recorded
```

ห้ามใช้ hand-written mock Snipe dataset เพื่อผ่าน checkpoint

------------------------------------------------------------------------

## Checkpoint 2 --- Passive Graph

โปรแกรมต้องสามารถ:

``` text
Load passive nodes
Load edges
Identify class start
Check connectivity
Calculate valid path
Calculate point cost
Reject impossible path
```

Acceptance test อย่างน้อยหนึ่งเส้นทางต้องคำนวณจากข้อมูลจริง

------------------------------------------------------------------------

## Checkpoint 3 --- Candidate Retrieval

Input:

``` text
Main Skill: Snipe
Playstyle: Fast
Goal: Mapping
Budget: Cheap
```

ระบบต้อง retrieve candidate data โดยไม่ส่ง database ทั้งหมดเข้า LLM

Output candidate sets:

``` text
mechanics
supports
passives
ascendancies
item bases
mods
uniques (when available)
```

ต้องมีเหตุผล/score หรือ retrieval metadata ที่สามารถ debug ได้ว่าทำไม candidate
ถูกเลือก

------------------------------------------------------------------------

## Checkpoint 4 --- AI Build Directions

AI รับเฉพาะ relevant BuildContext แล้วสร้างอย่างน้อย 3 แนวทาง

แต่ละแนวทางต้องมี:

``` text
Concept
Class
Ascendancy
Core mechanics
Damage direction
Defense direction
Mapping viability
Boss viability
Budget estimate/category
League-start viability
Strengths
Weaknesses
Critical dependencies
```

AI ห้าม invent skill/node/item ที่ไม่มีใน database

------------------------------------------------------------------------

## Checkpoint 5 --- Full Build + Validator

User เลือกหนึ่ง Build Direction

AI สร้าง:

``` text
Class
Ascendancy
Passive direction
Skills
Supports
Gear bases
Important uniques
Affix priorities
Defense
Resource solution
Leveling concept
Upgrade order
Rotation
```

Validator ต้องตรวจอย่างน้อย:

``` text
Referenced entities exist
Passive path is valid
Support compatibility
Weapon/base requirements
Basic attribute requirements
Obvious conflicts
```

หาก fail:

``` text
AI Build
   ↓
Validator
   ↓
Errors
   ↓
AI Revision
   ↓
Validator
```

จนผ่านหรือระบุอย่างชัดเจนว่าเหตุใดจึงไม่สามารถสร้าง build ที่ valid ได้

**เมื่อ Checkpoint 5 ผ่าน ถือว่า Core MVP เกิดแล้ว**

------------------------------------------------------------------------

## Checkpoint 6 --- Desktop Application

หลัง Core MVP ผ่านแล้วจึงทำ UX เต็มรูปแบบ

ขั้นต่ำ:

``` text
Main Skill selector
Playstyle controls
Budget
Mapping/Boss preference
League-start preference
Analyze button
Build Direction cards
Pick Build
Generate Build
Validation results
Settings
AI Provider configuration
```

------------------------------------------------------------------------

## Checkpoint 7 --- Windows Distribution

สร้าง:

``` text
PoEAIBuilder.exe
```

หรือ installer ที่เหมาะสม

ต้องรองรับ:

-   local database
-   data version
-   app version
-   user AI provider configuration
-   secure credential storage
-   logs
-   data update mechanism
-   app update mechanism (ภายหลังได้ถ้า MVP ยังไม่ต้อง auto-update)

------------------------------------------------------------------------

# 30. AI Usage Rules

AI/LLM มีหน้าที่หลักเป็น **Theorycrafter**

AI ไม่ควรถูกใช้แทน:

``` text
Database
Graph algorithm
Rule validator
Exact calculator
Version manager
```

ก่อนเรียก LLM ให้ deterministic code ลด context ก่อนเสมอ

ตัวอย่าง:

``` text
User Intent
    ↓
Database Query
    ↓
Candidate Filtering
    ↓
Ranking
    ↓
Compact BuildContext
    ↓
LLM
```

ห้ามส่ง passive tree/items/mods ทั้งเกมเข้า context หาก query/filter ได้ก่อน

------------------------------------------------------------------------

# 31. Model Strategy

ทำ AI provider abstraction ตั้งแต่ต้น

ห้าม hard-code โปรแกรมให้ใช้ model เดียว

Conceptual quality modes:

``` text
Economy
Balanced
Deep Analysis
Maximum
```

mapping ไปยัง model/reasoning level ต้องเป็น configuration
และเปลี่ยนได้ในอนาคต

ตัวอย่าง flow:

``` text
Cheap deterministic retrieval
        ↓
Normal model → candidate cleanup/summary (optional)
        ↓
Strong reasoning model → Build Directions
        ↓
Strong reasoning model → Full Build
        ↓
Code validator
        ↓
Reasoning model only when revision is needed
```

เป้าหมายคือประหยัด token โดยไม่ลดคุณภาพของ reasoning ที่สำคัญ

------------------------------------------------------------------------

# 32. Credential Rule

โปรแกรม community release ต้องใช้ credential ของ User เอง

หลักการ:

> **Token ใคร Token มัน**

ห้าม:

-   bundle developer API key
-   hard-code secret
-   commit API key
-   ส่ง User key ไป server ของผู้พัฒนาโดยไม่จำเป็น

ควรใช้ OS secure credential storage

AI Provider integration ต้องออกแบบให้เปลี่ยน provider ได้

------------------------------------------------------------------------

# 33. Data Licensing Rule

ก่อน redistribute dataset ใด ๆ กับ community release:

1.  ตรวจ source
2.  ตรวจ license/terms
3.  บันทึก attribution
4.  แยก software license ออกจาก game/community data license
5.  ถ้าไม่ชัดเจน ให้ flag ใน `USER_ACTION_REQUIRED.md`
6.  ห้าม assume ว่า public repository/public website = freely
    redistributable

PoE2DB ให้ถือเป็น reference/fallback จนกว่าจะตรวจ permission ชัดเจน

------------------------------------------------------------------------

# 34. No Fake Completion Rule

AI ห้ามรายงานว่า feature "เสร็จ" หาก:

-   ใช้ mock data แทน real data โดยไม่ได้ระบุ
-   function ยังเป็น stub
-   tests ไม่ผ่าน
-   validator ไม่ได้ตรวจจริง
-   UI แสดง hard-coded result
-   AI response ถูก hard-code
-   build ไม่สามารถ run ได้
-   database ยังไม่มี provenance/version
-   feature ถูก simulate เพื่อ demo เท่านั้น

ถ้าทำ prototype/stub ให้ label ชัดเจน:

``` text
PROTOTYPE
STUB
MOCK
NOT PRODUCTION READY
```

------------------------------------------------------------------------

# 35. Testing Rule

ทุก core subsystem ต้องมี automated tests เท่าที่เหมาะสม:

``` text
Importer tests
Database tests
Passive graph tests
Retrieval tests
Validator tests
AI structured-output parser tests
Migration/version tests
```

สำหรับ AI output ให้ใช้ schema validation

LLM output ที่ parse ไม่ได้ต้องไม่ทำให้ application crash

------------------------------------------------------------------------

# 36. First Execution Prompt

เมื่อ AI Coding Agent ได้รับไฟล์นี้ ให้ถือว่าคำสั่งเริ่มต้นคือ:

> Read this entire specification first. Start implementing the project
> immediately. Work autonomously and phase-by-phase. Begin with the Data
> Proof of Concept and the Snipe vertical slice. Do not stop after
> producing another plan. Use real data wherever available. Do not ask
> the user to perform tasks you can do yourself. When genuine user
> intervention is required, document it in USER_ACTION_REQUIRED.md with
> exact instructions, continue any unblocked work, and resume from the
> same project state after the user completes the required action. Keep
> README.md, TODO.md, tests, and docs/DEVELOPMENT_STATUS.md updated
> throughout development.

------------------------------------------------------------------------

# 37. Definition of Success

ภาพสุดท้าย:

``` text
User opens PoE AI Builder
        ↓
selects Snipe
        ↓
"Fast / Mapping / Cheap / League Start"
        ↓
Analyze
        ↓
program retrieves REAL game data
        ↓
AI proposes viable build directions
        ↓
User picks one
        ↓
AI creates full build
        ↓
program validates it
        ↓
invalid pieces are revised
        ↓
User receives a usable build
```

จากนั้นระบบเดียวกันต้องสามารถ generalize จาก `Snipe` ไปยัง skill
อื่นได้โดยไม่ต้องเขียน build logic แบบ hard-code ต่อ skill

**เป้าหมายไม่ใช่สร้าง AI ที่จำ Path of Exile 2 ได้ทั้งหมด**

เป้าหมายคือสร้างระบบที่:

> **มีข้อมูลเกมจริงอยู่ local → เลือกข้อมูลที่เกี่ยวข้องได้ → คำนวณ/ตรวจสอบสิ่งที่
> deterministic ได้ → แล้วใช้ AI reasoning เฉพาะส่วนที่ต้อง theorycraft จริง ๆ**
