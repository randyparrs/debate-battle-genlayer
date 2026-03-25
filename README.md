# ⚔️ Debate Battle — A GenLayer Community Mini-Game

> A multiplayer debate game where players argue opposing sides of a topic and **GenLayer's Intelligent Contracts + Optimistic Democracy** decide the winner — no human judge, no bias, just AI consensus.

![GenLayer](https://img.shields.io/badge/GenLayer-Intelligent%20Contract-00c896?style=for-the-badge)
![Type](https://img.shields.io/badge/Type-Mini--Game-orange?style=for-the-badge)
![Players](https://img.shields.io/badge/Players-2--8-blue?style=for-the-badge)
![Duration](https://img.shields.io/badge/Duration-5--15%20min-purple?style=for-the-badge)

---

## 📋 Table of Contents

1. [What Is Debate Battle?](#what-is-debate-battle)
2. [How GenLayer Powers the Game](#how-genlayer-powers-the-game)
3. [Game Rules](#game-rules)
4. [Project Architecture](#project-architecture)
5. [Part 1 — The Intelligent Contract](#part-1--the-intelligent-contract)
6. [Part 2 — Running in GenLayer Studio](#part-2--running-in-genlayer-studio)
7. [Leaderboard and XP System](#leaderboard-and-xp-system)
8. [Project Structure](#project-structure)
9. [Resources](#resources)

---

## What Is Debate Battle?

Debate Battle is a community mini-game built on GenLayer where:

- Players are split into **Team A** (FOR a topic) and **Team B** (AGAINST a topic)
- Each player submits a text argument defending their position
- A **GenLayer Intelligent Contract** fetches real web context and uses an LLM to judge the debate
- **Optimistic Democracy consensus** ensures the verdict is fair — multiple validators independently evaluate and must agree
- Winners earn **XP points** tracked on-chain

---

## How GenLayer Powers the Game

### Optimistic Democracy ✅
Multiple validators independently evaluate the debate arguments. A transaction is only finalized when validators reach consensus — ensuring no single node can manipulate the outcome.

### Equivalence Principle ✅
The `judge_debate` function uses `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`:
- **Leader** fetches web context + calls LLM to determine the winner
- **Validator** independently re-runs the same process
- Results are equivalent if: `winner_team` matches exactly AND scores are within ±10 points

### Web Data Access
The contract fetches Wikipedia context about the debate topic in real time to give the AI judge background knowledge before evaluating arguments.

---

## Game Rules

1. Host creates a room with a time limit (5, 10, or 15 minutes)
2. Players join and are automatically assigned to Team A or Team B
3. Host starts the debate
4. Each player submits one argument (10–500 characters)
5. Anyone calls `judge_debate` to trigger the AI verdict
6. Winners receive **100 XP**, losers receive **20 XP**

### Weekly Topics
The contract cycles through 10 curated debate topics:
- Bitcoin is better than Ethereum as a long-term store of value
- AI will create more jobs than it destroys in the next decade
- Decentralization is more important than user experience in Web3
- Layer 2 solutions are the future of blockchain scalability
- DAOs will replace traditional corporations within 20 years
- And more...

---

## Project Architecture

```
Player A ──┐
Player B ──┤──► DebateBattle Contract ──► gl.nondet.web.get (Wikipedia)
Player C ──┘         │                         │
                      │                         ▼
                      │                    gl.nondet.exec_prompt (LLM Judge)
                      │                         │
                      ▼                         ▼
              Optimistic Democracy ◄── gl.vm.run_nondet_unsafe
              (5 validators agree)              │
                      │                         ▼
                      └──────────► Winner + XP awarded on-chain
```

---

## Part 1 — The Intelligent Contract

The core of the game is `contracts/debate_battle.py` — an Intelligent Contract built with the current GenLayer Python SDK.

### Key Functions

| Function | Type | Description |
|----------|------|-------------|
| `create_room` | write | Create a new debate room |
| `join_room` | write | Join an existing room |
| `start_debate` | write | Host starts the debate |
| `submit_argument` | write | Submit your argument |
| `judge_debate` | write | Trigger AI judgment ✅ |
| `get_room_status` | view | Check room state |
| `get_player_xp` | view | Check player XP |
| `get_weekly_topic` | view | Get current topic |
| `get_game_summary` | view | Overall stats |

### Equivalence Principle Implementation

```python
def leader_fn():
    # Fetch Wikipedia context for the topic
    response = gl.nondet.web.get(wikipedia_url)
    web_context = response.body.decode("utf-8")[:2000]
    # LLM judges the debate
    result = gl.nondet.exec_prompt(prompt)
    return json.dumps({"winner_team": "A", "score_team_a": 75, ...}, sort_keys=True)

def validator_fn(leader_result) -> bool:
    if not isinstance(leader_result, gl.vm.Return):
        return False
    validator_raw = leader_fn()  # Re-run independently
    # winner_team must match exactly
    # scores within ±10 points
    return leader_data["winner_team"] == validator_data["winner_team"]

result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)  # ✅
```

---

## Part 2 — Running in GenLayer Studio

### Deploy the Contract

1. Go to [GenLayer Studio](https://studio.genlayer.com)
2. Create a new file `debate_battle.py`
3. Paste the contract code from `contracts/debate_battle.py`
4. Set Execution Mode to **Normal (Full Consensus)**
5. Deploy with your Studio address as `owner_address`

### Play a Full Game

```
Step 1: create_room        → time_limit_minutes: 5
Step 2: join_room          → room_id: ROOM0
Step 3: start_debate       → room_id: ROOM0
Step 4: submit_argument    → room_id: ROOM0
                             argument: "Your argument here (10-500 chars)"
Step 5: judge_debate       → room_id: ROOM0  ← AI judges here ✅
Step 6: get_room_status    → room_id: ROOM0  ← See the verdict
Step 7: get_player_xp      → player_address: 0xYourAddress
```

---

## Leaderboard and XP System

XP is tracked on-chain per player address:

| Result | XP Earned |
|--------|-----------|
| Winning team | +100 XP |
| Losing team | +20 XP |

Use `get_player_xp` with any player address to check their accumulated XP across all debates.

---

## Project Structure

```
debate-battle-genlayer/
├── contracts/
│   └── debate_battle.py      ← Intelligent Contract (GenLayer Studio)
└── README.md
```

---

## Resources

- [GenLayer Docs](https://docs.genlayer.com)
- [Optimistic Democracy](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy)
- [Equivalence Principle](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/equivalence-principle)
- [GenLayer Studio](https://studio.genlayer.com)
- [Discord](https://discord.gg/8Jm4v89VAu)
- [X (Twitter)](https://x.com/GenLayer)

---

*Built for the GenLayer Hackathon — Mini-games for GenLayer's Community track.* 

         

 


