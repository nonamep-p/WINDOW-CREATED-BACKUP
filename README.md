
 
 # ⚔️ Discord RPG Bot - Advanced Tactical Combat & Cooperative Gameplay

A comprehensive and modular Discord RPG bot offering **advanced tactical combat**, **cooperative guild gameplay**, **competitive PvP arena**, **player-driven economy**, **skills system**, **ultimate abilities**, **item usage**, and **dynamic progression systems**. Designed for ultra-low latency interactive gameplay through Discord embeds, buttons, and real-time updates with **clean, easy-to-understand interfaces**.

## Project Structure (Clean)

```   

.
├─ cogs/
│  ├─ admin_comprehensive.py      # Interactive admin panel (/admin_panel)
│  ├─ character.py                # Character management
│  ├─ combat.py                   # Combat commands
│  ├─ dungeon.py                  # Dungeon commands
│  ├─ economy.py                  # Economy/shop/daily
│  ├─ guild_interactive.py        # Interactive /guild UI
│  ├─ party.py                    # Party commands
│  ├─ profiles.py                 # Profile/leaderboards
│  ├─ pvp.py                      # PvP arena/duels
│  ├─ quests.py                   # Quests
│  ├─ lootbox.py                  # Lootbox
│  ├─ play.py                     # Main game panel
│  ├─ crafting.py                 # Crafting (if present)
│  └─ teams.py                    # Team coordination (if present)
├─ systems/
│  ├─ character.py                # Character system
│  ├─ combat.py                   # Core combat
│  ├─ advanced_combat.py          # Advanced combat
│  ├─ economy.py                  # Economy system
│  ├─ dungeon.py                  # Dungeon system
│  ├─ factions.py                 # Factions system
│  ├─ party.py                    # Party system
│  ├─ profiles.py                 # Profiles/achievements/rankings
│  ├─ guild.py                    # Guild persistence/helpers
│  ├─ database.py                 # JSON DB manager
│  └─ ... (crafting_trading, quests, rewards, team_coordination)
├─ utils/
│  ├─ dropdowns.py                # Reusable UI selects
│  ├─ helpers.py                  # Embed/format helpers
│  ├─ rate_limiter.py             # RL middleware
│  └─ ...
├─ data/
│  ├─ players.json                # Player save data
│  ├─ items.json                  # Items
│  ├─ monsters.json               # Monsters
│  ├─ achievements.json           # Achievements map
│  └─ dungeons/
│     └─ *.json                   # Dungeon definitions
├─ main.py                        # Bot entrypoint
├─ start_bot.py                   # Clean launcher
├─ start_clean.bat                # Windows runner
├─ requirements.txt
├─ config.py
└─ .env.example
```

## Quick Start

1) Create `.env` from example and set token:
```
copy .env.example .env
# Edit DISCORD_TOKEN
```

2) Install and run:
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python start_bot.py
```

3) Core commands: `/guild`, `/party`, `/pvp`, `/profile`, `/admin_panel`, `/daily`, `/shop`

## 🎮 Features Overview

### ⚔️ Advanced Combat System
- **Elemental Damage Types** (Fire, Ice, Lightning, Poison, Holy, Shadow, Magic)
- **Status Effects** (Burn, Frost, Shock, Poison, Bleed, Stun, Silence, Taunt, Haste, Slow, Regen, Shield)
- **Combo Mechanics** with increasing damage multipliers
- **Dynamic AI** with personality-driven behavior and adaptive tactics
- **Phase-based Boss Encounters** with enrage mechanics
- **Clean Battle Interface** with easy-to-read stats and action logs
- **Real-time Battle Updates** with streaming embeds

### 🎯 Skills System
- **Learnable Skills** with level requirements and SP costs
- **Skill Types**: Physical, Fire, Ice, Lightning, Healing, Defensive
- **Skill Database**: Slash, Fireball, Heal, Shield, Lightning Strike
- **Cooldown System** for balanced gameplay
- **Skill Power Scaling** based on character level and stats
- **Interactive Skill Selection** during combat

### 🔥 Ultimate Abilities
- **Class-Specific Ultimates** with unique effects
- **Ultimate Charging** through combat participation
- **Ultimate Effects**:
  - **Warrior**: Raging Fury - Massive damage to all enemies
  - **Mage**: Arcane Storm - Devastating magical explosion
  - **Archer**: Rain of Arrows - Barrage of deadly projectiles
  - **Rogue**: Shadow Assassination - Instant critical strike
- **Ultimate Status Tracking** with ready indicators

### 📦 Item Usage System
- **Consumable Items** (Potions, Scrolls, Elixirs)
- **Item Effects**: HP/SP restoration, stat buffs, status cures
- **Interactive Item Selection** during combat
- **Item Database**: Health Potion, Mana Potion, Strength Potion, etc.
- **Item Type Validation** (consumable, potion, scroll)
- **Inventory Management** with automatic item removal

### 🏰 Guild System
- **Cooperative Raids** with massive boss encounters
- **Guild Activities** (Raids, Quests, Wars, Crafting, Trading)
- **Progressive Guild Levels** with member limits and bonuses
- **Contribution Tracking** for XP and gold rewards
- **Role-based Permissions** (Leader, Officer, Member, Recruit)
- **Guild Skills** providing combat, crafting, and trading bonuses

### ⚔️ PvP Arena System
- **Competitive Rankings** (Bronze → Grandmaster)
- **Tournament System** with entry fees and prize pools
- **Real-time Matchmaking** with skill-based matchmaking
- **Best-of-3 Round System** with tactical depth
- **Rating-based Rewards** with rank multipliers
- **Leaderboards** with global rankings

### 🔨 Crafting & Trading System
- **Skill-based Crafting** with failure chances and XP rewards
- **Recipe Discovery** with material requirements and tool dependencies
- **Player-driven Market** with dynamic pricing
- **Auction-style Listings** with expiration times
- **Market Analytics** with supply/demand tracking
- **Crafting Progress** with real-time updates

### 🎭 Enhanced Character Progression
- **Elemental Affinities** based on character class
- **Status Immunities** from equipment and class
- **Skill Trees** with specialization paths
- **Equipment Resistances** and elemental bonuses
- **Advanced Stats** (Accuracy, Evasion, Penetration, Critical)
- **Prestige System** with enhanced rewards

### 🏰 Dynamic Dungeon System
- **Progressive Floors** with scaling difficulty
- **Boss Encounters** with unique mechanics
- **Session-based Tracking** per user
- **Partial Rewards** on early exit
- **Guild Dungeon Events** with cooperative challenges

### 🛒 Advanced Economy
- **Player-driven Market** with supply/demand dynamics
- **Guild Bank** for shared resources
- **Auction System** with bidding mechanics
- **Market Analytics** with price tracking
- **Trading Cards** for rare item exchange

### 📱 Clean Interactive UI
- **Streamlined Battle Interface** with clear stats display
- **Recent Action Logs** (last 3 actions only)
- **Clean Status Effects** display
- **Easy-to-Read Stats** with emoji indicators
- **Interactive Buttons** for immediate actions
- **Dynamic Dropdowns** for complex selections
- **Progress Bars** for crafting and activities
- **Status Indicators** for ongoing activities

### 🎁 Effort-Based Reward System
The bot features a sophisticated reward system that scales based on player effort and team coordination:

#### Effort Levels
- **😴 Minimal (0.5x rewards)** - Basic actions, button spam, low coordination
- **😐 Moderate (1.0x rewards)** - Standard gameplay, basic coordination  
- **😤 Intense (1.8x rewards)** - Complex strategies, elemental combos, good team coordination
- **🔥 Master (2.5x rewards)** - Perfect timing, expert coordination, risk-taking strategies

#### Team Coordination Bonuses
- **2 Players:** +10% rewards
- **3 Players:** +25% rewards
- **4 Players:** +40% rewards
- **5+ Players:** +60% rewards

#### Activity-Specific Effort Tracking
- **Combat:** Elemental combos, perfect timing, status effects
- **Dungeon:** Speed runs, no-damage clears, exploration efficiency
- **Guild Raid:** Perfect execution, leadership, coordination
- **PvP:** Strategic play, perfect execution, risk management
- **Crafting:** Complex recipes, perfect quality, rare materials

### 👥 Team Coordination System
Prevents confusion in multiplayer with clear role assignments and communication:

#### Team Roles
- **👑 Leader** - Team captain, makes decisions, gets leadership bonuses
- **🛡️ Tank** - Front line, draws aggro, gets defense bonuses
- **💚 Healer** - Support, keeps team alive, gets healing bonuses
- **⚔️ DPS** - Damage dealer, gets damage bonuses
- **🔮 Support** - Buffs, debuffs, utility, gets buff bonuses

#### Team Features
- **Clear Role Assignment** - Automatic role assignment based on team composition
- **Ready System** - All members must be ready before starting activities
- **Activity Coordination** - Specific instructions for each activity type
- **Effort Tracking** - Individual and team performance monitoring
- **Reward Distribution** - Fair distribution based on individual effort and team contribution

---

## 🗂️ Modular Structure

```
project/
│
├── main.py                # Bot entry point with advanced systems
├── config.py              # Config/settings management (pydantic-settings)
├── requirements.txt
├── README.md
│
├── data/                  # Data storage (JSON)
│   ├── players.json
│   ├── items.json
│   ├── monsters.json
│   ├── dungeons.json
│   ├── guilds.json
│   └── ...
│
├── systems/               # Core systems
│   ├── combat.py          # Basic combat system
│   ├── advanced_combat.py # Advanced combat with elements & status
│   ├── guild.py           # Guild system with cooperative gameplay
│   ├── pvp_arena.py       # PvP arena with rankings & tournaments
│   ├── crafting_trading.py # Crafting & player-driven market
│   ├── rewards.py         # Effort-based reward system
│   ├── team_coordination.py # Team coordination system
│   ├── dungeon.py
│   ├── character.py       # Character system with skills & ultimates
│   ├── inventory.py       # Inventory with item usage
│   ├── economy.py
│   ├── tutorial.py
│   └── database.py
│
├── cogs/                  # Discord command cogs (slash + interactive UI)
│   ├── character.py
│   ├── combat.py          # Combat with clean interface
│   ├── guild.py           # Guild management commands
│   ├── pvp.py             # PvP arena commands
│   ├── crafting.py        # Crafting & market commands
│   ├── teams.py           # Team coordination commands
│   ├── dungeon.py
│   ├── inventory.py
│   ├── economy.py
│   ├── tutorial.py
│   ├── admin.py
│   └── factions.py
│
└── utils/
    ├── helpers.py
    └── rate_limiter.py
```

---

## ⚔️ Advanced Combat System

### Elemental Damage Types
- **Fire** - Effective vs Ice, weak vs Poison
- **Ice** - Effective vs Fire, weak vs Lightning  
- **Lightning** - Effective vs Ice, weak vs Water
- **Poison** - Effective vs Holy, weak vs Shadow
- **Holy** - Effective vs Shadow/Undead, weak vs Shadow
- **Shadow** - Effective vs Holy, weak vs Light
- **Magic** - Universal damage type

### Status Effects
- **Burn** - Damage over time, stackable (max 5)
- **Frost** - Reduced speed and evasion
- **Shock** - Chance to stun, reduced accuracy
- **Poison** - Damage over time, stackable (max 3)
- **Bleed** - Damage over time, stackable (max 4)
- **Stun** - Skip turn, cannot act
- **Silence** - Cannot use skills
- **Taunt** - Forced to attack taunter
- **Haste** - Increased speed and evasion
- **Slow** - Reduced speed and accuracy
- **Regen** - Healing over time
- **Shield** - Reduces incoming damage

### Combo Mechanics
- **Combo Counter** increases with consecutive attacks
- **Damage Multiplier** up to 50% bonus at max combo
- **Elemental Affinity** provides 20% bonus for matching elements
- **Critical Hits** with enhanced damage and effects

### Dynamic AI Behavior
- **Aggressive** - Always attacks
- **Defensive** - Defends against high combos
- **Tactical** - Adapts based on player health and own health
- **Phase-based** - Enrages at low health with increased damage

---

## 🎯 Skills System

### Available Skills
- **Slash** (Level 1) - A powerful melee attack (25 power, 10 SP)
- **Fireball** (Level 5) - Launch a ball of fire (30 power, 15 SP, 2-turn cooldown)
- **Heal** (Level 8) - Restore HP to yourself (40 power, 20 SP, 3-turn cooldown)
- **Shield** (Level 10) - Create a protective barrier (0 power, 15 SP, 4-turn cooldown)
- **Lightning Strike** (Level 15) - Call down lightning from the sky (35 power, 25 SP, 3-turn cooldown)

### Skill Features
- **Level Requirements** for skill learning
- **SP Cost System** for skill usage
- **Cooldown Management** to prevent spam
- **Skill Types** (Physical, Fire, Ice, Lightning, Healing, Defensive)
- **Power Scaling** based on character stats
- **Interactive Learning** through modals

---

## 🔥 Ultimate Abilities

### Class-Specific Ultimates
- **Warrior**: Raging Fury - Massive damage to all enemies
- **Mage**: Arcane Storm - Devastating magical explosion
- **Archer**: Rain of Arrows - Barrage of deadly projectiles
- **Rogue**: Shadow Assassination - Instant critical strike

### Ultimate Mechanics
- **Charging System** through combat participation
- **100% Charge Requirement** for ultimate activation
- **Automatic Reset** after ultimate use
- **Ready Status Tracking** with visual indicators
- **Class-Based Effects** for unique gameplay

---

## 📦 Item Usage System

### Consumable Items
- **Health Potion** - Restored 50 HP
- **Mana Potion** - Restored 30 SP
- **Strength Potion** - Attack increased for 3 turns
- **Defense Potion** - Defense increased for 3 turns
- **Speed Potion** - Speed increased for 3 turns
- **Healing Scroll** - Fully restored HP
- **Mana Scroll** - Fully restored SP
- **Revival Scroll** - Revived with full health
- **Blessing Scroll** - All stats increased for 5 turns
- **Antidote** - Cured all status effects
- **Elixir** - Restored all HP and SP

### Item Features
- **Type Validation** (consumable, potion, scroll)
- **Automatic Removal** after use
- **Effect Application** with status messages
- **Inventory Integration** with real-time updates
- **Interactive Selection** during combat

---

## 🏰 Enhanced Dungeon System

- Multiple floors with scaling difficulty
- Configurable boss floors (e.g., explicit boss on `boss_floor`)
- Session-based dungeon tracking per user
- Continue/Exit flow with partial rewards on exit

### Dungeon Types (sample)

| Type   | Difficulty | Theme                         |
|--------|------------|-------------------------------|
| Forest | 1.0x       | Nature spirits and creatures  |
| Cave   | 1.2x       | Shadow and cavern monsters    |
| Castle | 1.4x       | Undead knights and ghosts     |
| Abyss  | 1.6x       | Eldritch horrors              |

Rewards scale by floor and multipliers; boss floors grant boosted rewards.

---

## 🎭 Character Classes & Stats

- Multiple classes with unique base stats
- Stat system: HP, SP, Attack, Defense, Speed, Intelligence, Luck, Agility
- Level progression via XP; equipment affects derived stats
- Faction bonuses applied to stats when joined

---

## 🛡️ Items & Equipment

- JSON-defined items (`data/items.json`), flat schema (name, type, rarity, price, effects)
- Common types: Weapon, Armor, Accessory, Shield, Consumable
- Inventory with stacking for consumables/materials
- Equipment slots with stat bonuses applied

---

## 💰 Economy & Shop (Interactive)

- Earn gold via combat and dungeons
- Interactive Shop:
  - Dropdown to select items
  - Buy button opens quantity modal
  - Validates balance and inventory updates
- Daily reward command (cooldown-based)

Planned: Trading and Crafting systems.

---

## 🏳️ Factions (Interactive)

- Join a faction via select + Join button
- Immediate application of faction stat bonuses
- Extensible faction definitions from code/data

Planned: Territory control and faction events.

---

## ✨ Achievements (Scaffold)

- Default achievements with rewards (gold/xp)
- Granting helper to award achievements on milestones

Planned: Titles & techniques with display and mastery.

---

## 📚 Tutorials & Help

- Guided tutorial flow with steps
- Help command with basic guidance and tips

---

## 🔧 Admin Controls

- Admin slash command with interactive modals:
  - Give Gold, Give XP, Give Item
- Bot statistics overview

---

## 📱 Clean Interactive UI

- **Streamlined embeds** for status and summaries
- **Clean battle interface** with easy-to-read stats
- **Recent action logs** (last 3 actions only)
- **Emoji indicators** for clear visual feedback
- **Buttons for actions** and navigation
- **Dropdowns for selection** (shop, factions)
- **Real-time updates** during battles and dungeons

---

## 🛠️ Setup Instructions

1. Prerequisites
   - Python 3.11+
   - Discord Bot Token (Bot Privileged Intents as needed)

2. Install
   ```bash
   pip install -r requirements.txt
   ```

3. Configure
   - Create a `.env` in the project root:
   ```env
   DISCORD_TOKEN=your_discord_bot_token
   BOT_PREFIX=!
   DEBUG_MODE=False
   ```

4. Run
   ```bash
   python main.py
   ```

On Windows you can use `run_bot.bat` to auto-create a venv and run the bot.

## 🎮 Command Reference

### Core Commands
- `/character create` - Create your character
- `/hunt` - Fight monsters for XP and loot (clean interface)
- `/advancedhunt` - Advanced hunting with elemental combat
- `/dungeon` - Explore dungeons for rare items
- `/inventory` - Manage your equipment
- `/shop` - Buy and sell items

### Skills & Abilities
- `/skills` - View and use your character skills
- `/ultimate` - Use your ultimate ability
- `/useitem <item_name>` - Use an item from your inventory

### Advanced Combat
- `/elementalattack` - Use elemental attacks (consumes SP)
- `/combatstatus` - Check active status effects

### Guild System
- `/guild create <name> [description]` - Create a guild
- `/guild info` - View guild information
- `/guild members` - List guild members
- `/guild leave` - Leave current guild
- `/guildraid` - Start a guild raid (leaders/officers only)
- `/guildcontribute <damage/progress>` - Contribute to guild activity
- `/guilds` - List all guilds

### PvP Arena
- `/challenge <opponent> [match_type]` - Challenge player to PvP
- `/pvp <action> [target]` - Perform PvP actions
- `/arena` - View arena information and rankings
- `/arenaleaderboard` - View arena leaderboard
- `/tournament create <name> <entry_fee> [max_participants]` - Create tournament
- `/tournament list` - List active tournaments

### Crafting & Trading
- `/craft <recipe_id> [quantity]` - Craft an item
- `/craftstatus` - Check crafting progress
- `/recipes [skill] [difficulty]` - View available recipes
- `/market list` - View market listings
- `/market sell <item_id> <quantity> <price>` - List item for sale
- `/market buy <item_id> [quantity]` - Buy item from market
- `/market cancel <item_id>` - Cancel your listing
- `/mylistings` - View your market listings
- `/crafting` - View detailed crafting progress

### Team Commands
- `/team create <activity>` - Create a new team for an activity
- `/team join <team_id>` - Join an existing team
- `/team leave <team_id>` - Leave a team
- `/team info <team_id>` - View team information
- `/team ready <team_id>` - Set yourself as ready
- `/team start <team_id>` - Start the team activity (leader only)

### Effort & Reward Commands
- `/effort` - Check your effort-based reward summary
- `/rewards` - Learn about the effort-based reward system

### Admin Commands
- `/admin givegold <user> <amount>` - Give gold to player
- `/admin givexp <user> <amount>` - Give XP to player
- `/admin giveitem <user> <item_id> [quantity]` - Give item to player

---

## 🧭 Roadmap (High-Level)

- PvP Arena with rankings and Gladiator Tokens
- Crafting (discovery + recipes) and Trading
- Titles, Techniques, and cosmetic customization
- Seasonal events, leaderboards, and tournaments
- Guilds/faction territories and world map

---

Contributions and extensions are welcome. Keep modules cohesive and data-driven for easy content updates.
