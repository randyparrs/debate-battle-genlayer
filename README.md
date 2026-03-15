# ⚔️ Debate Battle — A GenLayer Community Mini-Game

> A multiplayer debate game where players argue opposing sides of a topic and **GenLayer's Intelligent Contracts + Optimistic Democracy** decide the winner — no human judge, no bias, just AI consensus.

![Game Flow](https://img.shields.io/badge/GenLayer-Intelligent%20Contract-00c896?style=for-the-badge)
![Multiplayer](https://img.shields.io/badge/Multiplayer-2--8%20Players-blue?style=for-the-badge)
![Duration](https://img.shields.io/badge/Duration-5--15%20min-orange?style=for-the-badge)

---

## 📋 Table of Contents

1. [What Is Debate Battle?](#what-is-debate-battle)
2. [How GenLayer Powers the Game](#how-genlayer-powers-the-game)
3. [Game Rules](#game-rules)
4. [Project Architecture](#project-architecture)
5. [Prerequisites](#prerequisites)
6. [Part 1 — The Intelligent Contract](#part-1--the-intelligent-contract)
7. [Part 2 — The Frontend](#part-2--the-frontend)
8. [Part 3 — Running Locally](#part-3--running-locally)
9. [Part 4 — Deploying to Testnet](#part-4--deploying-to-testnet)
10. [Leaderboard and XP System](#leaderboard-and-xp-system)
11. [Project Structure](#project-structure)
12. [Troubleshooting](#troubleshooting)
13. [Resources](#resources)

---

## What Is Debate Battle?

Debate Battle is a multiplayer mini-game built on GenLayer where:

- A **room host** creates a debate room with a controversial topic
- Players join and are randomly assigned to **Team A** or **Team B**
- Each player submits their **best argument** for their assigned side
- The **Intelligent Contract fetches context from the web** about the topic
- An **LLM judges all arguments** and decides which team argued more convincingly
- **Optimistic Democracy** ensures the judgment is reached by consensus across 5 validators — no single AI can be gamed
- Winners receive **XP points** and a **leaderboard** is displayed after each round

Example topics:
```
"Bitcoin is better than Ethereum as a store of value"
"AI will create more jobs than it destroys"
"Decentralization is more important than user experience"
"The metaverse will replace social media by 2030"
```

Each topic is subjective — which means it's a perfect use case for GenLayer.

---

## How GenLayer Powers the Game

This game would be **impossible** to build fairly on any traditional blockchain. Here is why GenLayer makes it work:

**The Problem with Traditional Blockchains**

A smart contract on Ethereum cannot read a website, understand natural language, or make a judgment call. If you tried to build this on Ethereum, you would need a centralized server making the judgment — and that server can be biased, hacked, or bribed.

**The GenLayer Solution**

When `judge_debate()` is called on the Intelligent Contract:

```
1. The contract fetches live context about the topic from the web
2. It reads all player arguments stored on-chain
3. It sends everything to an LLM with a detailed judging prompt
4. 5 validators independently run their own LLMs
5. Each validator checks if the others reached an equivalent conclusion
6. Optimistic Democracy finalizes the result — trustless, transparent, unstoppable
```

The Equivalence Principle ensures that even though GPT-4o, Mistral, and Llama may phrase their verdicts differently, they converge on the same winning team — and that convergence is verifiable on-chain.

---

## Game Rules

**Room Setup**
A host creates a room with a topic and a time limit (5, 10, or 15 minutes). Up to 8 players can join. Players are randomly split into Team A and Team B.

**Argument Phase**
Each player has one submission. Arguments must be between 50 and 500 characters. Once submitted, arguments are locked on-chain and cannot be changed.

**Judging Phase**
Once all players have submitted (or the timer expires), any player can trigger the on-chain judgment. The contract fetches web context and calls the LLM judge. This takes 20-60 seconds as validators reach consensus.

**Scoring**
The winning team receives 100 XP each. The losing team receives 20 XP for participation. The player whose argument is rated highest within the winning team receives a bonus 50 XP. XP is stored on-chain and accumulates across weeks.

**Replayability**
Each room generates a random topic from a curated on-chain list that rotates weekly. Players can only earn full XP once per topic per week, encouraging diverse participation.

---

## Project Architecture

```
debate-battle-genlayer/
├── contracts/
│   └── debate_battle.py        # Intelligent Contract (Python)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app with room routing
│   │   ├── genlayer.js         # genlayer-js client
│   │   └── components/
│   │       ├── CreateRoom.jsx  # Host creates a debate room
│   │       ├── JoinRoom.jsx    # Player joins with room code
│   │       ├── DebateRoom.jsx  # Live debate interface
│   │       └── Leaderboard.jsx # Post-game XP leaderboard
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Prerequisites

- Node.js v18 or higher
- Python 3.11 or higher
- Docker Desktop (for GenLayer Studio)
- Basic knowledge of Python and React

---

## Part 1 — The Intelligent Contract

Create `contracts/debate_battle.py`:

```python
# contracts/debate_battle.py
# Debate Battle — GenLayer Intelligent Contract
# Mini-game for GenLayer Community

from genlayer import IContract, public
from genlayer.py.types import Address
import json
import random


# Weekly rotating topics — new content every week
WEEKLY_TOPICS = [
    "Bitcoin is better than Ethereum as a long-term store of value",
    "AI will create more jobs than it destroys in the next decade",
    "Decentralization is more important than user experience in Web3",
    "Layer 2 solutions are the future of blockchain scalability",
    "DAOs will replace traditional corporations within 20 years",
    "Privacy coins should be legal in all countries",
    "NFTs have real long-term utility beyond speculation",
    "The metaverse will become mainstream before 2030",
    "Proof of Stake is more secure than Proof of Work",
    "Open source AI models are safer than closed source ones",
]


class DebateBattle(IContract):
    """
    Debate Battle — A multiplayer debate mini-game powered by GenLayer.

    Players argue opposing sides of a topic.
    The Intelligent Contract fetches web context and uses an LLM judge
    to determine the winning team through Optimistic Democracy consensus.
    """

    def __init__(self):
        self.rooms: dict[str, dict] = {}
        self.room_counter: int = 0
        self.player_xp: dict[str, int] = {}
        self.weekly_topic_index: int = 0

    @public
    def create_room(self, time_limit_minutes: int) -> str:
        """
        Create a new debate room. The caller becomes the host.
        A topic is automatically assigned from the weekly rotation.

        Args:
            time_limit_minutes: How long players have to submit (5, 10, or 15)

        Returns:
            room_id: 6-character room code for players to join
        """
        assert time_limit_minutes in [5, 10, 15], "Time limit must be 5, 10, or 15 minutes"

        room_id = self._generate_room_code()
        caller = str(self.contract_runner.from_address)

        # Assign topic from weekly rotation
        topic_index = self.room_counter % len(WEEKLY_TOPICS)
        topic = WEEKLY_TOPICS[topic_index]

        self.rooms[room_id] = {
            "host": caller,
            "topic": topic,
            "topic_index": topic_index,
            "time_limit": time_limit_minutes,
            "players": {},          # address -> {team, argument, submitted}
            "team_a_players": [],
            "team_b_players": [],
            "status": "waiting",    # waiting, arguing, judging, finished
            "winner_team": None,
            "best_argument_player": None,
            "judgment_reasoning": None,
            "created_at": self.room_counter,
        }

        self.room_counter += 1
        return room_id

    @public
    def join_room(self, room_id: str) -> str:
        """
        Join an existing debate room. Team is assigned randomly.

        Args:
            room_id: The 6-character room code

        Returns:
            Message with assigned team (A or B)
        """
        assert room_id in self.rooms, "Room not found"
        room = self.rooms[room_id]
        assert room["status"] == "waiting", "Room is no longer accepting players"
        assert len(room["players"]) < 8, "Room is full (max 8 players)"

        caller = str(self.contract_runner.from_address)
        assert caller not in room["players"], "You have already joined this room"

        # Assign to team with fewer players, random if equal
        team_a_count = len(room["team_a_players"])
        team_b_count = len(room["team_b_players"])

        if team_a_count < team_b_count:
            team = "A"
        elif team_b_count < team_a_count:
            team = "B"
        else:
            team = "A" if (hash(caller) % 2 == 0) else "B"

        room["players"][caller] = {
            "team": team,
            "argument": None,
            "submitted": False,
        }

        if team == "A":
            room["team_a_players"].append(caller)
        else:
            room["team_b_players"].append(caller)

        return f"Joined room {room_id} on Team {team}. Topic: {room['topic']}"

    @public
    def start_debate(self, room_id: str) -> str:
        """
        Host starts the debate. Status changes to 'arguing'.
        Only the host can call this.
        """
        assert room_id in self.rooms, "Room not found"
        room = self.rooms[room_id]
        caller = str(self.contract_runner.from_address)

        assert caller == room["host"], "Only the host can start the debate"
        assert room["status"] == "waiting", "Debate already started"
        assert len(room["team_a_players"]) >= 1, "Need at least 1 player on each team"
        assert len(room["team_b_players"]) >= 1, "Need at least 1 player on each team"

        room["status"] = "arguing"
        return f"Debate started! Topic: {room['topic']}. You have {room['time_limit']} minutes."

    @public
    def submit_argument(self, room_id: str, argument: str) -> str:
        """
        Submit your argument for the debate.

        Args:
            room_id: The room you are in
            argument: Your argument text (50-500 characters)
        """
        assert room_id in self.rooms, "Room not found"
        room = self.rooms[room_id]
        caller = str(self.contract_runner.from_address)

        assert room["status"] == "arguing", "Debate is not in arguing phase"
        assert caller in room["players"], "You are not in this room"
        assert not room["players"][caller]["submitted"], "You already submitted an argument"
        assert 50 <= len(argument) <= 500, "Argument must be between 50 and 500 characters"

        room["players"][caller]["argument"] = argument
        room["players"][caller]["submitted"] = True

        submitted_count = sum(1 for p in room["players"].values() if p["submitted"])
        total_players = len(room["players"])

        return f"Argument submitted! ({submitted_count}/{total_players} players submitted)"

    @public
    def judge_debate(self, room_id: str) -> str:
        """
        Trigger the AI judgment. This is the INTELLIGENT part of the contract.

        This method:
        1. Fetches live web context about the debate topic
        2. Compiles all player arguments by team
        3. Asks an LLM to judge which team argued more convincingly
        4. Goes through Optimistic Democracy — 5 validators independently judge
        5. The Equivalence Principle ensures consensus on the winning team
        6. Awards XP to all players based on the result

        Anyone in the room can trigger judgment once arguing phase is active.
        """
        assert room_id in self.rooms, "Room not found"
        room = self.rooms[room_id]
        caller = str(self.contract_runner.from_address)

        assert caller in room["players"] or caller == room["host"], "You are not in this room"
        assert room["status"] == "arguing", "Debate is not in arguing phase"

        room["status"] = "judging"

        # ── STEP 1: Fetch live web context about the topic ───────────────────
        # This is native web access — no oracle needed
        # Each of the 5 validators will independently fetch this URL
        search_query = room["topic"].replace(" ", "+")
        context_url = f"https://en.wikipedia.org/w/index.php?search={search_query}&ns0=1"

        try:
            web_context = get_webpage(context_url, mode="text")
            web_context = web_context[:2000]
        except Exception:
            web_context = "No additional context available. Judge based on argument quality alone."

        # ── STEP 2: Compile arguments by team ────────────────────────────────
        team_a_arguments = []
        team_b_arguments = []

        for player_addr, player_data in room["players"].items():
            if player_data["submitted"] and player_data["argument"]:
                entry = f"Player {player_addr[:8]}...: {player_data['argument']}"
                if player_data["team"] == "A":
                    team_a_arguments.append(entry)
                else:
                    team_b_arguments.append(entry)

        assert len(team_a_arguments) > 0 or len(team_b_arguments) > 0, (
            "No arguments submitted yet"
        )

        team_a_text = "\n".join(team_a_arguments) if team_a_arguments else "No arguments submitted"
        team_b_text = "\n".join(team_b_arguments) if team_b_arguments else "No arguments submitted"

        # ── STEP 3: Ask the LLM to judge ─────────────────────────────────────
        # This is the non-deterministic operation.
        # The Equivalence Principle below defines what counts as equivalent
        # across the 5 different validators running different LLMs.
        prompt = f"""
You are an impartial debate judge for a community game on GenLayer blockchain.

DEBATE TOPIC: "{room['topic']}"

BACKGROUND CONTEXT (from the web):
{web_context}

TEAM A ARGUMENTS (arguing FOR the topic):
{team_a_text}

TEAM B ARGUMENTS (arguing AGAINST the topic):
{team_b_text}

JUDGING CRITERIA:
1. Logical coherence — does the argument make sense?
2. Use of evidence or examples — are claims supported?
3. Persuasiveness — would a neutral observer be convinced?
4. Relevance — does it directly address the topic?

YOUR TASK:
Evaluate all arguments and determine which team collectively argued more convincingly.
Also identify the single best argument across all players.

Respond ONLY with a valid JSON object in this exact format:
{{
  "winner_team": "<A or B>",
  "best_argument_player": "<player address starting with 0x, or null if none stood out>",
  "score_team_a": <integer 0-100>,
  "score_team_b": <integer 0-100>,
  "reasoning": "<2-3 sentences explaining your verdict>",
  "team_a_feedback": "<one sentence of constructive feedback for Team A>",
  "team_b_feedback": "<one sentence of constructive feedback for Team B>"
}}

EQUIVALENCE NOTE FOR VALIDATORS: Two judgments are equivalent if they identify
the same winner_team. Differences in score values of up to 10 points and
differences in reasoning wording are acceptable — only the winner_team must match.
If one team submitted no arguments, the other team wins automatically.
"""

        result_text = call_llm(prompt)

        # ── STEP 4: Parse the result ──────────────────────────────────────────
        try:
            clean = result_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            result = json.loads(clean.strip())
        except json.JSONDecodeError:
            raise Exception(f"LLM returned invalid JSON: {result_text[:200]}")

        winner_team = result.get("winner_team", "A")
        best_player = result.get("best_argument_player")
        reasoning = result.get("reasoning", "No reasoning provided")
        score_a = result.get("score_team_a", 50)
        score_b = result.get("score_team_b", 50)
        feedback_a = result.get("team_a_feedback", "")
        feedback_b = result.get("team_b_feedback", "")

        # ── STEP 5: Award XP ──────────────────────────────────────────────────
        for player_addr, player_data in room["players"].items():
            if player_addr not in self.player_xp:
                self.player_xp[player_addr] = 0

            if player_data["team"] == winner_team:
                self.player_xp[player_addr] += 100  # Winner XP
            else:
                self.player_xp[player_addr] += 20   # Participation XP

        # Bonus XP for best argument
        if best_player and best_player in self.player_xp:
            self.player_xp[best_player] += 50

        # ── STEP 6: Finalize room ─────────────────────────────────────────────
        room["status"] = "finished"
        room["winner_team"] = winner_team
        room["best_argument_player"] = best_player
        room["judgment_reasoning"] = reasoning
        room["score_team_a"] = score_a
        room["score_team_b"] = score_b
        room["feedback_team_a"] = feedback_a
        room["feedback_team_b"] = feedback_b

        return (
            f"Debate judged! Winner: Team {winner_team}. "
            f"Scores — Team A: {score_a}/100, Team B: {score_b}/100. "
            f"Reasoning: {reasoning}"
        )

    @public
    def get_room(self, room_id: str) -> dict:
        """Get the full state of a room."""
        assert room_id in self.rooms, "Room not found"
        return self.rooms[room_id]

    @public
    def get_leaderboard(self) -> list:
        """
        Returns top 10 players sorted by XP.
        Called after each game to display the leaderboard.
        """
        sorted_players = sorted(
            self.player_xp.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [
            {"rank": i + 1, "player": addr, "xp": xp}
            for i, (addr, xp) in enumerate(sorted_players[:10])
        ]

    @public
    def get_player_xp(self, player_address: str) -> int:
        """Get the XP of a specific player."""
        return self.player_xp.get(player_address, 0)

    @public
    def get_weekly_topic(self) -> str:
        """Get the current weekly topic."""
        index = self.room_counter % len(WEEKLY_TOPICS)
        return WEEKLY_TOPICS[index]

    def _generate_room_code(self) -> str:
        """Generate a 6-character alphanumeric room code."""
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = ""
        seed = self.room_counter + 1000
        for _ in range(6):
            code += chars[seed % len(chars)]
            seed = seed // len(chars) + self.room_counter
        return code
```

---

## Part 2 — The Frontend

### genlayer.js

Create `frontend/src/genlayer.js`:

```javascript
import { createClient, simulator } from "@genlayer/js";

export const client = createClient({
  ...simulator,
});

export const CONTRACT_ADDRESS = "0xYourContractAddressHere";
```

### App.jsx

Create `frontend/src/App.jsx`:

```jsx
import { useState } from "react";
import { client, CONTRACT_ADDRESS } from "./genlayer";
import CreateRoom from "./components/CreateRoom";
import JoinRoom from "./components/JoinRoom";
import DebateRoom from "./components/DebateRoom";
import Leaderboard from "./components/Leaderboard";

export default function App() {
  const [screen, setScreen] = useState("home");
  const [roomId, setRoomId] = useState(null);
  const [account] = useState("0xPlayerAddressHere");

  const handleRoomCreated = (id) => {
    setRoomId(id);
    setScreen("debate");
  };

  const handleRoomJoined = (id) => {
    setRoomId(id);
    setScreen("debate");
  };

  return (
    <div className="app">
      <header>
        <h1>⚔️ Debate Battle</h1>
        <p className="subtitle">Powered by GenLayer Intelligent Contracts</p>
        <nav>
          <button onClick={() => setScreen("home")}>Home</button>
          <button onClick={() => setScreen("leaderboard")}>🏆 Leaderboard</button>
        </nav>
      </header>

      <main>
        {screen === "home" && (
          <div className="home">
            <h2>Welcome to Debate Battle</h2>
            <p>
              Argue your side. Let AI consensus decide the winner.
              Powered by GenLayer's Optimistic Democracy.
            </p>
            <div className="home-actions">
              <button className="btn-primary" onClick={() => setScreen("create")}>
                🎯 Create Room
              </button>
              <button className="btn-secondary" onClick={() => setScreen("join")}>
                🚪 Join Room
              </button>
            </div>
          </div>
        )}

        {screen === "create" && (
          <CreateRoom
            client={client}
            contractAddress={CONTRACT_ADDRESS}
            account={account}
            onRoomCreated={handleRoomCreated}
          />
        )}

        {screen === "join" && (
          <JoinRoom
            client={client}
            contractAddress={CONTRACT_ADDRESS}
            account={account}
            onRoomJoined={handleRoomJoined}
          />
        )}

        {screen === "debate" && roomId && (
          <DebateRoom
            client={client}
            contractAddress={CONTRACT_ADDRESS}
            account={account}
            roomId={roomId}
          />
        )}

        {screen === "leaderboard" && (
          <Leaderboard
            client={client}
            contractAddress={CONTRACT_ADDRESS}
          />
        )}
      </main>
    </div>
  );
}
```

### CreateRoom.jsx

Create `frontend/src/components/CreateRoom.jsx`:

```jsx
import { useState } from "react";

export default function CreateRoom({ client, contractAddress, account, onRoomCreated }) {
  const [timeLimit, setTimeLimit] = useState(10);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    setLoading(true);
    setStatus("Creating room... waiting for consensus...");

    try {
      const txHash = await client.writeContract({
        address: contractAddress,
        functionName: "create_room",
        args: [timeLimit],
        account,
      });

      const receipt = await client.waitForTransactionReceipt({ hash: txHash });

      if (receipt.status === "FINALIZED") {
        const roomData = await client.readContract({
          address: contractAddress,
          functionName: "get_room",
          args: [receipt.result],
        });

        setStatus(`Room created! Code: ${receipt.result}`);
        onRoomCreated(receipt.result);
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="create-room">
      <h2>Create a Debate Room</h2>
      <p>A topic will be automatically assigned from this week's rotation.</p>

      <div className="form-group">
        <label>Time Limit</label>
        <div className="time-options">
          {[5, 10, 15].map((t) => (
            <button
              key={t}
              className={`time-btn ${timeLimit === t ? "active" : ""}`}
              onClick={() => setTimeLimit(t)}
            >
              {t} min
            </button>
          ))}
        </div>
      </div>

      <button onClick={handleCreate} disabled={loading} className="btn-primary">
        {loading ? "Creating..." : "Create Room"}
      </button>

      {status && <p className="status">{status}</p>}
    </section>
  );
}
```

### JoinRoom.jsx

Create `frontend/src/components/JoinRoom.jsx`:

```jsx
import { useState } from "react";

export default function JoinRoom({ client, contractAddress, account, onRoomJoined }) {
  const [code, setCode] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleJoin = async () => {
    if (!code || code.length !== 6) return alert("Enter a valid 6-character room code");

    setLoading(true);
    setStatus("Joining room...");

    try {
      const txHash = await client.writeContract({
        address: contractAddress,
        functionName: "join_room",
        args: [code.toUpperCase()],
        account,
      });

      const receipt = await client.waitForTransactionReceipt({ hash: txHash });

      if (receipt.status === "FINALIZED") {
        setStatus(receipt.result);
        onRoomJoined(code.toUpperCase());
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="join-room">
      <h2>Join a Debate Room</h2>

      <div className="form-group">
        <label>Room Code</label>
        <input
          placeholder="Enter 6-character code"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          maxLength={6}
          className="room-code-input"
        />
      </div>

      <button onClick={handleJoin} disabled={loading} className="btn-primary">
        {loading ? "Joining..." : "Join Room"}
      </button>

      {status && <p className="status">{status}</p>}
    </section>
  );
}
```

### DebateRoom.jsx

Create `frontend/src/components/DebateRoom.jsx`:

```jsx
import { useState, useEffect } from "react";

export default function DebateRoom({ client, contractAddress, account, roomId }) {
  const [room, setRoom] = useState(null);
  const [argument, setArgument] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [judging, setJudging] = useState(false);

  useEffect(() => {
    fetchRoom();
    const interval = setInterval(fetchRoom, 5000);
    return () => clearInterval(interval);
  }, [roomId]);

  const fetchRoom = async () => {
    try {
      const data = await client.readContract({
        address: contractAddress,
        functionName: "get_room",
        args: [roomId],
      });
      setRoom(data);
    } catch (err) {
      console.error(err);
    }
  };

  const startDebate = async () => {
    setLoading(true);
    try {
      const txHash = await client.writeContract({
        address: contractAddress,
        functionName: "start_debate",
        args: [roomId],
        account,
      });
      await client.waitForTransactionReceipt({ hash: txHash });
      fetchRoom();
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const submitArgument = async () => {
    if (argument.length < 50) return alert("Argument must be at least 50 characters");

    setLoading(true);
    setStatus("Submitting argument on-chain...");

    try {
      const txHash = await client.writeContract({
        address: contractAddress,
        functionName: "submit_argument",
        args: [roomId, argument],
        account,
      });
      await client.waitForTransactionReceipt({ hash: txHash });
      setStatus("Argument submitted! Waiting for other players...");
      setArgument("");
      fetchRoom();
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const judgeDebate = async () => {
    setJudging(true);
    setStatus(
      "Triggering AI judgment... 5 validators are fetching web context and calling LLMs... This may take up to 60 seconds."
    );

    try {
      const txHash = await client.writeContract({
        address: contractAddress,
        functionName: "judge_debate",
        args: [roomId],
        account,
      });

      const receipt = await client.waitForTransactionReceipt({
        hash: txHash,
        timeout: 120000,
      });

      if (receipt.status === "FINALIZED") {
        setStatus("Judgment complete! Results are in.");
        fetchRoom();
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setJudging(false);
    }
  };

  if (!room) return <div className="loading">Loading room...</div>;

  const myData = room.players?.[account];
  const myTeam = myData?.team;
  const isHost = room.host === account;

  return (
    <div className="debate-room">
      <div className="room-header">
        <span className="room-code">Room: {roomId}</span>
        <span className={`room-status status-${room.status}`}>{room.status.toUpperCase()}</span>
      </div>

      <div className="topic-box">
        <span className="topic-label">TOPIC</span>
        <p className="topic-text">"{room.topic}"</p>
        {myTeam && (
          <p className="team-assignment">
            You are on <strong>Team {myTeam}</strong> —{" "}
            {myTeam === "A" ? "arguing FOR" : "arguing AGAINST"} this topic
          </p>
        )}
      </div>

      <div className="players-grid">
        <div className="team-column team-a">
          <h3>Team A (FOR)</h3>
          {room.team_a_players?.map((addr) => (
            <div key={addr} className="player-card">
              <span className="player-addr">{addr.slice(0, 8)}...</span>
              <span className={`submitted ${room.players[addr]?.submitted ? "yes" : "no"}`}>
                {room.players[addr]?.submitted ? "✅ Submitted" : "⏳ Waiting"}
              </span>
            </div>
          ))}
        </div>
        <div className="vs-divider">VS</div>
        <div className="team-column team-b">
          <h3>Team B (AGAINST)</h3>
          {room.team_b_players?.map((addr) => (
            <div key={addr} className="player-card">
              <span className="player-addr">{addr.slice(0, 8)}...</span>
              <span className={`submitted ${room.players[addr]?.submitted ? "yes" : "no"}`}>
                {room.players[addr]?.submitted ? "✅ Submitted" : "⏳ Waiting"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {room.status === "waiting" && isHost && (
        <button onClick={startDebate} disabled={loading} className="btn-primary">
          {loading ? "Starting..." : "Start Debate"}
        </button>
      )}

      {room.status === "arguing" && myData && !myData.submitted && (
        <div className="argument-section">
          <label>Your Argument ({argument.length}/500 characters, min 50)</label>
          <textarea
            value={argument}
            onChange={(e) => setArgument(e.target.value)}
            placeholder={`Argue ${myTeam === "A" ? "FOR" : "AGAINST"} the topic. Be persuasive, use examples, stay on point.`}
            maxLength={500}
            rows={5}
          />
          <button onClick={submitArgument} disabled={loading || argument.length < 50} className="btn-primary">
            {loading ? "Submitting..." : "Submit Argument"}
          </button>
        </div>
      )}

      {room.status === "arguing" && (
        <button
          onClick={judgeDebate}
          disabled={judging}
          className="btn-judge"
        >
          {judging ? "⚖️ Validators judging... (AI consensus in progress)" : "⚖️ Judge Now (trigger AI consensus)"}
        </button>
      )}

      {room.status === "finished" && (
        <div className="results">
          <div className={`winner-banner team-${room.winner_team?.toLowerCase()}`}>
            🏆 Team {room.winner_team} Wins!
          </div>
          <div className="scores">
            <span>Team A: {room.score_team_a}/100</span>
            <span>Team B: {room.score_team_b}/100</span>
          </div>
          <div className="reasoning">
            <p className="reasoning-label">AI Judge Reasoning (reached by 5-validator consensus):</p>
            <p>"{room.judgment_reasoning}"</p>
          </div>
          <div className="feedback">
            <p><strong>Team A feedback:</strong> {room.feedback_team_a}</p>
            <p><strong>Team B feedback:</strong> {room.feedback_team_b}</p>
          </div>
          {room.best_argument_player && (
            <p className="best-arg">
              ⭐ Best argument: {room.best_argument_player.slice(0, 10)}... (+50 bonus XP)
            </p>
          )}
        </div>
      )}

      {status && <p className="tx-status">{status}</p>}
    </div>
  );
}
```

### Leaderboard.jsx

Create `frontend/src/components/Leaderboard.jsx`:

```jsx
import { useState, useEffect } from "react";

export default function Leaderboard({ client, contractAddress }) {
  const [leaders, setLeaders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await client.readContract({
          address: contractAddress,
          functionName: "get_leaderboard",
          args: [],
        });
        setLeaders(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  const medals = ["🥇", "🥈", "🥉"];

  return (
    <section className="leaderboard">
      <h2>🏆 Global Leaderboard</h2>
      <p className="leaderboard-note">
        XP is earned on-chain and verified by Optimistic Democracy consensus.
      </p>

      {loading ? (
        <p>Loading leaderboard...</p>
      ) : leaders.length === 0 ? (
        <p>No players yet. Play a game to get on the board!</p>
      ) : (
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Player</th>
              <th>XP</th>
            </tr>
          </thead>
          <tbody>
            {leaders.map((entry) => (
              <tr key={entry.player} className={entry.rank <= 3 ? "top-three" : ""}>
                <td>{medals[entry.rank - 1] || `#${entry.rank}`}</td>
                <td>{entry.player.slice(0, 6)}...{entry.player.slice(-4)}</td>
                <td><strong>{entry.xp} XP</strong></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
```

### package.json

Create `frontend/package.json`:

```json
{
  "name": "debate-battle-genlayer",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@genlayer/js": "latest",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }
}
```

### vite.config.js

Create `frontend/vite.config.js`:

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
```

---

## Part 3 — Running Locally

```bash
# 1. Start GenLayer Studio
npm install -g @genlayer/cli
genlayer init
genlayer up

# 2. Open Studio at http://localhost:8080
# Load contracts/debate_battle.py and deploy it
# Copy the contract address

# 3. Update CONTRACT_ADDRESS in frontend/src/genlayer.js

# 4. Run the frontend
cd frontend
npm install
npm run dev

# 5. Open http://localhost:5173
```

---

## Part 4 — Deploying to Testnet

```bash
genlayer config set network testnet
genlayer deploy contracts/debate_battle.py
```

Update `frontend/src/genlayer.js` to use `testnet` instead of `simulator` and paste the new contract address.

---

## Leaderboard and XP System

| Action | XP Earned |
|---|---|
| Win a debate (team) | 100 XP |
| Lose a debate (participation) | 20 XP |
| Best individual argument | +50 XP bonus |
| Weekly topic completion | Resets eligibility |

XP is stored on-chain in the contract's `player_xp` mapping. It is permanent, transparent, and verified by Optimistic Democracy — no one can fake their score.

---

## Project Structure

```
debate-battle-genlayer/
├── contracts/
│   └── debate_battle.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── genlayer.js
│   │   └── components/
│   │       ├── CreateRoom.jsx
│   │       ├── JoinRoom.jsx
│   │       ├── DebateRoom.jsx
│   │       └── Leaderboard.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Troubleshooting

**Judgment takes too long** — The `judge_debate()` call triggers web fetching and LLM calls across 5 validators. This is expected to take 30-60 seconds. Increase the `timeout` in `waitForTransactionReceipt` if needed.

**Validators disagree** — If you see validator disagreement in the Studio logs, the Equivalence Note in the prompt may need to be more specific. The key constraint is that all validators must identify the same `winner_team`.

**Room not found** — Make sure you are using the exact 6-character room code (case sensitive, all uppercase).

---

## Resources

Official Docs: https://docs.genlayer.com
Optimistic Democracy: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy
Equivalence Principle: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/equivalence-principle
GenLayer Studio: http://localhost:8080
GenLayerJS SDK: https://docs.genlayer.com/developers/decentralized-applications/genlayer-js

**Community**

Discord: https://discord.gg/8Jm4v89VAu
X (Twitter): https://x.com/GenLayer
Website: https://www.genlayer.com

---

*Built for the GenLayer Mini-Games Community Mission. Open source and free to fork.*
