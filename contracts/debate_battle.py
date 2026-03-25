# { "Depends": "py-genlayer:test" }

# ============================================================
#  Debate Battle — GenLayer Community Mini-Game
#  Mini-games for GenLayer's Community Track
#
#  A multiplayer debate game where players argue opposing
#  sides of a topic and GenLayer's Intelligent Contracts +
#  Optimistic Democracy decide the winner.
#
#  Requirements met:
#    ✅ Optimistic Democracy consensus
#    ✅ Equivalence Principle (gl.vm.run_nondet_unsafe)
# ============================================================

import json
from genlayer import *


WEEKLY_TOPICS = [
    "Bitcoin is better than Ethereum as a long-term store of value",
    "AI will create more jobs than it destroys in the next decade",
    "Decentralization is more important than user experience in Web3",
    "Layer 2 solutions are the future of blockchain scalability",
    "DAOs will replace traditional corporations within 20 years",
    "Privacy coins should be legal in all countries",
    "NFTs have real long-term utility beyond speculation",
    "Proof of Stake is more secure than Proof of Work",
    "Open source AI models are safer than closed source ones",
    "The metaverse will become mainstream before 2030",
]


class DebateBattle(gl.Contract):

    # ── State ──────────────────────────────────────────────
    owner: str
    room_counter: u256

    # Room data stored as flat strings "field:value"
    # room_{id}_host, room_{id}_topic, room_{id}_status,
    # room_{id}_score_a, room_{id}_score_b, room_{id}_reasoning
    room_data: DynArray[str]

    # Player data: "room_id:address:team:submitted:argument:xp"
    player_log: DynArray[str]

    # ── Constructor ────────────────────────────────────────
    def __init__(self, owner_address: str):
        self.owner = owner_address
        self.room_counter = u256(0)

    # ══════════════════════════════════════════════════════
    #  READ FUNCTIONS
    # ══════════════════════════════════════════════════════

    @gl.public.view
    def get_weekly_topic(self) -> str:
        index = int(self.room_counter) % len(WEEKLY_TOPICS)
        return WEEKLY_TOPICS[index]

    @gl.public.view
    def get_room_count(self) -> u256:
        return self.room_counter

    @gl.public.view
    def get_room_status(self, room_id: str) -> str:
        status = self._get_room_field(room_id, "status")
        topic = self._get_room_field(room_id, "topic")
        winner = self._get_room_field(room_id, "winner")
        score_a = self._get_room_field(room_id, "score_a")
        score_b = self._get_room_field(room_id, "score_b")
        reasoning = self._get_room_field(room_id, "reasoning")
        if not status:
            return "Room not found"
        return (
            f"Room: {room_id} | Status: {status} | Topic: {topic} | "
            f"Winner: {winner} | Score A: {score_a} | Score B: {score_b} | "
            f"Reasoning: {reasoning}"
        )

    @gl.public.view
    def get_player_xp(self, player_address: str) -> str:
        total_xp = 0
        for i in range(len(self.player_log)):
            entry = self.player_log[i]
            parts = entry.split(":")
            if len(parts) >= 6 and parts[1] == player_address:
                try:
                    total_xp += int(parts[5])
                except Exception:
                    pass
        return f"Player {player_address[:8]}... XP: {total_xp}"

    @gl.public.view
    def get_game_summary(self) -> str:
        return (
            f"=== Debate Battle ===\n"
            f"Total Rooms: {int(self.room_counter)}\n"
            f"Current Topic: {self.get_weekly_topic()}"
        )

    # ══════════════════════════════════════════════════════
    #  CREATE ROOM
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def create_room(self, time_limit_minutes: u256) -> str:
        assert int(time_limit_minutes) in [5, 10, 15], "Time limit must be 5, 10, or 15"

        caller = str(gl.message.sender_address)
        room_id = f"ROOM{int(self.room_counter)}"
        index = int(self.room_counter) % len(WEEKLY_TOPICS)
        topic = WEEKLY_TOPICS[index]

        self._set_room_field(room_id, "host", caller)
        self._set_room_field(room_id, "topic", topic)
        self._set_room_field(room_id, "status", "waiting")
        self._set_room_field(room_id, "time_limit", str(int(time_limit_minutes)))
        self._set_room_field(room_id, "winner", "")
        self._set_room_field(room_id, "score_a", "0")
        self._set_room_field(room_id, "score_b", "0")
        self._set_room_field(room_id, "reasoning", "")

        self.room_counter = u256(int(self.room_counter) + 1)
        return f"Room {room_id} created! Topic: {topic}"

    # ══════════════════════════════════════════════════════
    #  JOIN ROOM
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def join_room(self, room_id: str) -> str:
        caller = str(gl.message.sender_address)
        status = self._get_room_field(room_id, "status")
        assert status == "waiting", "Room not found or not accepting players"
        assert not self._player_in_room(room_id, caller), "Already joined"

        team_a = self._count_team(room_id, "A")
        team_b = self._count_team(room_id, "B")
        team = "A" if team_a <= team_b else "B"

        # "room_id:address:team:submitted:argument:xp"
        self.player_log.append(f"{room_id}:{caller}:{team}:false::0")

        topic = self._get_room_field(room_id, "topic")
        return f"Joined {room_id} on Team {team}! Topic: {topic}"

    # ══════════════════════════════════════════════════════
    #  START DEBATE
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def start_debate(self, room_id: str) -> str:
        caller = str(gl.message.sender_address)
        host = self._get_room_field(room_id, "host")
        assert caller == host, "Only the host can start"
        assert self._get_room_field(room_id, "status") == "waiting", "Already started"
        assert self._count_team(room_id, "A") >= 1 or self._count_team(room_id, "B") >= 1, "Need at least 1 player"

        self._set_room_field(room_id, "status", "arguing")
        topic = self._get_room_field(room_id, "topic")
        time_limit = self._get_room_field(room_id, "time_limit")
        return f"Debate started! Topic: {topic}. You have {time_limit} minutes!"

    # ══════════════════════════════════════════════════════
    #  SUBMIT ARGUMENT
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def submit_argument(self, room_id: str, argument: str) -> str:
        caller = str(gl.message.sender_address)
        assert self._get_room_field(room_id, "status") == "arguing", "Not in arguing phase"
        assert self._player_in_room(room_id, caller), "You are not in this room"
        assert 10 <= len(argument) <= 500, "Argument must be 10-500 characters"

        for i in range(len(self.player_log)):
            entry = self.player_log[i]
            parts = entry.split(":")
            if len(parts) >= 6 and parts[0] == room_id and parts[1] == caller:
                assert parts[3] == "false", "Already submitted"
                # "room_id:address:team:submitted:argument:xp"
                safe_arg = argument.replace(":", "-")
                self.player_log[i] = f"{room_id}:{caller}:{parts[2]}:true:{safe_arg}:{parts[5]}"
                return f"Argument submitted for {room_id}!"
        return "Player not found"

    # ══════════════════════════════════════════════════════
    #  JUDGE DEBATE — Equivalence Principle ✅
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def judge_debate(self, room_id: str) -> str:
        assert self._get_room_field(room_id, "status") == "arguing", "Not in arguing phase"

        topic = self._get_room_field(room_id, "topic")

        team_a_args = []
        team_b_args = []
        for i in range(len(self.player_log)):
            entry = self.player_log[i]
            parts = entry.split(":")
            if len(parts) >= 6 and parts[0] == room_id and parts[3] == "true" and parts[4]:
                entry_text = f"Player {parts[1][:8]}...: {parts[4]}"
                if parts[2] == "A":
                    team_a_args.append(entry_text)
                else:
                    team_b_args.append(entry_text)

        assert len(team_a_args) > 0 or len(team_b_args) > 0, "No arguments submitted yet"

        team_a_text = "\n".join(team_a_args) if team_a_args else "No arguments submitted"
        team_b_text = "\n".join(team_b_args) if team_b_args else "No arguments submitted"

        def leader_fn():
            search_url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
            try:
                response = gl.nondet.web.get(search_url)
                web_context = response.body.decode("utf-8")[:2000]
            except Exception:
                web_context = "No additional context available."

            prompt = f"""You are an impartial debate judge for a GenLayer community game.

DEBATE TOPIC: "{topic}"

BACKGROUND CONTEXT:
{web_context}

TEAM A ARGUMENTS (FOR the topic):
{team_a_text}

TEAM B ARGUMENTS (AGAINST the topic):
{team_b_text}

Evaluate both teams and respond ONLY with a JSON object:
{{
  "winner_team": "A",
  "score_team_a": 75,
  "score_team_b": 60,
  "reasoning": "two sentences explaining the verdict"
}}

Rules:
- winner_team: exactly "A" or "B"
- scores: integers 0-100
- If a team has no arguments, the other team wins automatically
No extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            winner = data.get("winner_team", "A")
            score_a = int(data.get("score_team_a", 50))
            score_b = int(data.get("score_team_b", 50))
            reasoning = data.get("reasoning", "")
            if winner not in ("A", "B"):
                winner = "A"
            score_a = max(0, min(100, score_a))
            score_b = max(0, min(100, score_b))
            return json.dumps({
                "winner_team": winner,
                "score_team_a": score_a,
                "score_team_b": score_b,
                "reasoning": reasoning
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            """
            Winner must match exactly.
            Scores within ±10 points. ✅
            """
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)
                if leader_data["winner_team"] != validator_data["winner_team"]:
                    return False
                if abs(leader_data["score_team_a"] - validator_data["score_team_a"]) > 10:
                    return False
                if abs(leader_data["score_team_b"] - validator_data["score_team_b"]) > 10:
                    return False
                return True
            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        winner = data["winner_team"]
        score_a = data["score_team_a"]
        score_b = data["score_team_b"]
        reasoning = data["reasoning"]

        self._set_room_field(room_id, "status", "finished")
        self._set_room_field(room_id, "winner", winner)
        self._set_room_field(room_id, "score_a", str(score_a))
        self._set_room_field(room_id, "score_b", str(score_b))
        self._set_room_field(room_id, "reasoning", reasoning)

        # Award XP
        for i in range(len(self.player_log)):
            entry = self.player_log[i]
            parts = entry.split(":")
            if len(parts) >= 6 and parts[0] == room_id:
                xp = int(parts[5]) if parts[5].isdigit() else 0
                if parts[2] == winner:
                    xp += 100
                else:
                    xp += 20
                self.player_log[i] = f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}:{parts[4]}:{xp}"

        return (
            f"Winner: Team {winner}! "
            f"Score A: {score_a}/100, Score B: {score_b}/100. "
            f"{reasoning}"
        )

    # ══════════════════════════════════════════════════════
    #  INTERNAL HELPERS
    # ══════════════════════════════════════════════════════

    def _get_room_field(self, room_id: str, field: str) -> str:
        key = f"{room_id}_{field}:"
        for i in range(len(self.room_data)):
            if self.room_data[i].startswith(key):
                return self.room_data[i][len(key):]
        return ""

    def _set_room_field(self, room_id: str, field: str, value: str) -> None:
        key = f"{room_id}_{field}:"
        for i in range(len(self.room_data)):
            if self.room_data[i].startswith(key):
                self.room_data[i] = f"{key}{value}"
                return
        self.room_data.append(f"{key}{value}")

    def _player_in_room(self, room_id: str, addr: str) -> bool:
        for i in range(len(self.player_log)):
            parts = self.player_log[i].split(":")
            if len(parts) >= 2 and parts[0] == room_id and parts[1] == addr:
                return True
        return False

    def _count_team(self, room_id: str, team: str) -> int:
        count = 0
        for i in range(len(self.player_log)):
            parts = self.player_log[i].split(":")
            if len(parts) >= 3 and parts[0] == room_id and parts[2] == team:
                count += 1
        return count

    


