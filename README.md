# Debate Battle  A GenLayer Community Mini-Game

A multiplayer debate game where players argue opposing sides of a topic and GenLayer Intelligent Contracts plus Optimistic Democracy decide the winner. No human judge, no bias, just AI consensus.

---

## Table of Contents

1. What Is Debate Battle
2. How GenLayer Powers the Game
3. Game Rules
4. Project Architecture
5. Part 1 The Intelligent Contract
6. Part 2 Running in GenLayer Studio
7. Leaderboard and XP System
8. Project Structure
9. Resources

---

## What Is Debate Battle

Debate Battle is a community mini-game built on GenLayer where players are split into Team A arguing for a topic and Team B arguing against it. Each player submits a text argument defending their position. A GenLayer Intelligent Contract fetches real web context and uses an LLM to judge the debate. Optimistic Democracy consensus ensures the verdict is fair because multiple validators independently evaluate and must agree. Winners earn XP points tracked on-chain.

---

## How GenLayer Powers the Game

### Optimistic Democracy

Multiple validators independently evaluate the debate arguments. A transaction is only finalized when validators reach consensus, ensuring no single node can manipulate the outcome.

### Equivalence Principle

The judge_debate function uses gl.vm.run_nondet_unsafe with a leader function and a validator function. The leader fetches web context and calls the LLM to determine the winner. The validator independently re-runs the same process. Results are equivalent if winner_team matches exactly and scores are within plus or minus 10 points.

### Web Data Access

The contract fetches Wikipedia context about the debate topic in real time to give the AI judge background knowledge before evaluating the arguments.

---

## Game Rules

The host creates a room with a time limit of 5, 10, or 15 minutes. Players join and are automatically assigned to Team A or Team B. The host starts the debate. Each player submits one argument between 10 and 500 characters. Anyone can call judge_debate to trigger the AI verdict. Winners receive 100 XP and losers receive 20 XP.

### Weekly Topics

The contract cycles through 10 curated debate topics including Bitcoin is better than Ethereum as a long-term store of value, AI will create more jobs than it destroys in the next decade, Decentralization is more important than user experience in Web3, Layer 2 solutions are the future of blockchain scalability, and DAOs will replace traditional corporations within 20 years.

---

## Project Architecture

Players submit arguments to the DebateBattle Contract which fetches context from Wikipedia using gl.nondet.web.get and then calls the LLM judge using gl.nondet.exec_prompt. The result goes through gl.vm.run_nondet_unsafe where five validators must agree through Optimistic Democracy before the winner and XP are awarded on-chain.

---

## Part 1 The Intelligent Contract

The core of the game is contracts/debate_battle.py built with the current GenLayer Python SDK.

### Key Functions

create_room is a write function that creates a new debate room.

join_room is a write function that joins an existing room.

start_debate is a write function that the host uses to start the debate.

submit_argument is a write function for submitting your argument.

judge_debate is a write function that triggers the AI judgment.

get_room_status is a view function that checks the room state.

get_player_xp is a view function that checks player XP.

get_weekly_topic is a view function that returns the current topic.

get_game_summary is a view function that shows overall stats.

### Equivalence Principle Implementation

```python
def leader_fn():
    response = gl.nondet.web.get(wikipedia_url)
    web_context = response.body.decode("utf-8")[:2000]
    result = gl.nondet.exec_prompt(prompt)
    return json.dumps({"winner_team": "A", "score_team_a": 75}, sort_keys=True)

def validator_fn(leader_result) -> bool:
    if not isinstance(leader_result, gl.vm.Return):
        return False
    validator_raw = leader_fn()
    return leader_data["winner_team"] == validator_data["winner_team"]

result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
```

---

## Part 2 Running in GenLayer Studio

Go to GenLayer Studio at https://studio.genlayer.com and create a new file called debate_battle.py. Paste the contract code from contracts/debate_battle.py. Set execution mode to Normal Full Consensus. Deploy with your Studio address as owner_address.

### Play a Full Game

Step 1: create_room with time_limit_minutes set to 5

Step 2: join_room with the room_id that was returned

Step 3: start_debate with the same room_id

Step 4: submit_argument with the room_id and your argument text between 10 and 500 characters

Step 5: judge_debate with the room_id to trigger the AI verdict

Step 6: get_room_status with the room_id to see the result

Step 7: get_player_xp with your address to check your XP

---

## Leaderboard and XP System

XP is tracked on-chain per player address. The winning team earns 100 XP per debate and the losing team earns 20 XP. Use get_player_xp with any player address to check their accumulated XP across all debates.

---

## Project Structure

```
debate-battle-genlayer/
├── contracts/
│   └── debate_battle.py
└── README.md
```

---

## Resources

GenLayer Docs: https://docs.genlayer.com

Optimistic Democracy: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy

Equivalence Principle: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/equivalence-principle

GenLayer Studio: https://studio.genlayer.com

Discord: https://discord.gg/8Jm4v89VAu

X Twitter: https://x.com/GenLayer

---

Built for the GenLayer Hackathon, Mini-games for GenLayer Community track.

         

 


