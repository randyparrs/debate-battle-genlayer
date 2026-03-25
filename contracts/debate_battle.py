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
    "The metaverse will become mainstream before 2030",
    "Proof of Stake is more secure than Proof of Work",
    "Open source AI models are safer than closed source ones",
]


@allow_storage
@dataclass
class Player:
    address: str
    team: str        # "A" or "B"
    argument: str
    submitted: bool
    xp: u256


@allow_storage
@dataclass
class Room:
    id: str
    host: str
    topic: str
    time_limit: u256
    status: str      # "waiting" | "arguing" | "judging" | "finished"
    winner_team: str
    score_team_a: u256
    score_team_b: u256
    reasoning: str
    player_count: u256


class DebateBattle(gl.Contract):

    # ── State ──────────────────────────────────────────────
    owner: str
    room_counter: u256
    rooms: DynArray[Room]
    players: DynArray[Player]
    room_player_log: DynArray[str]   # "room_id:player_address" flat list

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
    def get_room(self, room_id: str) -> str:
        for i in range(len(self.rooms)):
            r = self.rooms[i]
            if r.id == room_id:
                return (
                    f"Room: {r.id} | "
                    f"Topic: {r.topic} | "
                    f"Status: {r.status} | "
                    f"Players: {int(r.player_count)} | "
                    f"Winner: {r.winner_team} | "
                    f"Score A: {int(r.score_team_a)} | "
                    f"Score B: {int(r.score_team_b)} | "
                    f"Reasoning: {r.reasoning}"
                )
        return "Room not found"

    @gl.public.view
    def get_player_xp(self, player_address: str) -> u256:
        for i in range(len(self.players)):
            p = self.players[i]
            if p.address == player_address:
                return p.xp
        return u256(0)

    @gl.public.view
    def get_game_summary(self) -> str:
        return (
            f"=== Debate Battle DAO ===\n"
            f"Total Rooms: {int(self.room_counter)}\n"
            f"Total Players: {len(self.players)}\n"
            f"Current Topic: {self.get_weekly_topic()}"
        )

    # ══════════════════════════════════════════════════════
    #  CREATE ROOM
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def create_room(self, time_limit_minutes: u256) -> str:
        assert int(time_limit_minutes) in [5, 10, 15], "Time limit must be 5, 10, or 15"

        caller = str(gl.message.sender_address)
        room_id = self._generate_room_code()
        index = int(self.room_counter) % len(WEEKLY_TOPICS)
        topic = WEEKLY_TOPICS[index]

        room = Room(
            id=room_id,
            host=caller,
            topic=topic,
            time_limit=time_limit_minutes,
            status="waiting",
            winner_team="",
            score_team_a=u256(0),
            score_team_b=u256(0),
            reasoning="",
            player_count=u256(0),
        )
        self.rooms.append(room)
        self.room_counter = u256(int(self.room_counter) + 1)
        return f"Room {room_id} created! Topic: {topic}"

    # ══════════════════════════════════════════════════════
    #  JOIN ROOM
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def join_room(self, room_id: str) -> str:
        caller = str(gl.message.sender_address)
        room_idx = self._find_room(room_id)
        assert room_idx >= 0, "Room not found"

        r = self.rooms[room_idx]
        assert r.status == "waiting", "Room is not accepting players"
        assert int(r.player_count) < 8, "Room is full (max 8 players)"
        assert not self._player_in_room(room_id, caller), "Already joined"

        # Assign team for balance
        team_a = self._count_team(room_id, "A")
        team_b = self._count_team(room_id, "B")
        team = "A" if team_a <= team_b else "B"

        player = Player(
            address=caller,
            team=team,
            argument="",
            submitted=False,
            xp=u256(0),
        )
        self.players.append(player)
        self.room_player_log.append(f"{room_id}:{caller}")

        r.player_count = u256(int(r.player_count) + 1)
        self.rooms[room_idx] = r

        return f"Joined room {room_id} on Team {team}! Topic: {r.topic}"

    # ══════════════════════════════════════════════════════
    #  START DEBATE
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def start_debate(self, room_id: str) -> str:
        caller = str(gl.message.sender_address)
        room_idx = self._find_room(room_id)
        assert room_idx >= 0, "Room not found"

        r = self.rooms[room_idx]
        assert caller == r.host, "Only the host can start"
        assert r.status == "waiting", "Debate already started"
        assert self._count_team(room_id, "A") >= 1, "Need at least 1 player on Team A"
        assert self._count_team(room_id, "B") >= 1, "Need at least 1 player on Team B"

        r.status = "arguing"
        self.rooms[room_idx] = r
        return f"Debate started! Topic: {r.topic}. You have {int(r.time_limit)} minutes!"

    # ══════════════════════════════════════════════════════
    #  SUBMIT ARGUMENT
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def submit_argument(self, room_id: str, argument: str) -> str:
        caller = str(gl.message.sender_address)
        room_idx = self._find_room(room_id)
        assert room_idx >= 0, "Room not found"

        r = self.rooms[room_idx]
        assert r.status == "arguing", "Debate not in arguing phase"
        assert self._player_in_room(room_id, caller), "You are not in this room"
        assert 10 <= len(argument) <= 500, "Argument must be 10-500 characters"

        # Update player argument
        for i in range(len(self.players)):
            p = self.players[i]
            key = f"{room_id}:{p.address}"
            if p.address == caller and self._key_in_log(key):
                assert not p.submitted, "Already submitted"
                p.argument = argument
                p.submitted = True
                self.players[i] = p
                break

        return f"Argument submitted for room {room_id}!"

    # ══════════════════════════════════════════════════════
    #  JUDGE DEBATE — uses Equivalence Principle ✅
    # ══════════════════════════════════════════════════════

    @gl.public.write
    def judge_debate(self, room_id: str) -> str:
        caller = str(gl.message.sender_address)
        room_idx = self._find_room(room_id)
        assert room_idx >= 0, "Room not found"

        r = self.rooms[room_idx]
        assert r.status == "arguing", "Debate not in arguing phase"

        topic = r.topic

        # Collect arguments per team
        team_a_args = []
        team_b_args = []
        for i in range(len(self.players)):
            p = self.players[i]
            key = f"{room_id}:{p.address}"
            if self._key_in_log(key) and p.submitted and p.argument:
                entry = f"Player {p.address[:8]}...: {p.argument}"
                if p.team == "A":
                    team_a_args.append(entry)
                else:
                    team_b_args.append(entry)

        assert len(team_a_args) > 0 or len(team_b_args) > 0, "No arguments submitted"

        team_a_text = "\n".join(team_a_args) if team_a_args else "No arguments submitted"
        team_b_text = "\n".join(team_b_args) if team_b_args else "No arguments submitted"

        # ── Equivalence Principle: leader + validator ✅ ──

        def leader_fn():
            # Fetch web context for the topic
            search_url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
            try:
                response = gl.nondet.web.get(search_url)
                web_context = response.body.decode("utf-8")[:2000]
            except Exception:
                web_context = "No additional context available."

            prompt = f"""You are an impartial debate judge for a community game on GenLayer blockchain.

DEBATE TOPIC: "{topic}"

BACKGROUND CONTEXT:
{web_context}

TEAM A ARGUMENTS (arguing FOR the topic):
{team_a_text}

TEAM B ARGUMENTS (arguing AGAINST the topic):
{team_b_text}

JUDGING CRITERIA:
1. Logical coherence
2. Use of evidence or examples
3. Persuasiveness
4. Relevance to the topic

Respond ONLY with a JSON object:
{{
  "winner_team": "A",
  "score_team_a": 75,
  "score_team_b": 60,
  "reasoning": "two sentences explaining the verdict"
}}

Rules:
- winner_team: exactly "A" or "B"
- scores: integers 0-100
- reasoning: two sentences max
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
            Validators independently judge the debate.
            Equivalent if: same winner_team + scores within ±10 ✅
            """
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)

                # Winner must match exactly
                if leader_data["winner_team"] != validator_data["winner_team"]:
                    return False
                # Scores within ±10 points
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

        # Update room
        r.status = "finished"
        r.winner_team = winner
        r.score_team_a = u256(score_a)
        r.score_team_b = u256(score_b)
        r.reasoning = reasoning
        self.rooms[room_idx] = r

        # Award XP
        for i in range(len(self.players)):
            p = self.players[i]
            key = f"{room_id}:{p.address}"
            if self._key_in_log(key):
                if p.team == winner:
                    p.xp = u256(int(p.xp) + 100)
                else:
                    p.xp = u256(int(p.xp) + 20)
                self.players[i] = p

        return (
            f"Winner: Team {winner}! "
            f"Score A: {score_a}/100, Score B: {score_b}/100. "
            f"{reasoning}"
        )

    # ══════════════════════════════════════════════════════
    #  INTERNAL HELPERS
    # ══════════════════════════════════════════════════════

    def _find_room(self, room_id: str) -> int:
        for i in range(len(self.rooms)):
            if self.rooms[i].id == room_id:
                return i
        return -1

    def _player_in_room(self, room_id: str, addr: str) -> bool:
        return self._key_in_log(f"{room_id}:{addr}")

    def _key_in_log(self, key: str) -> bool:
        for i in range(len(self.room_player_log)):
            if self.room_player_log[i] == key:
                return True
        return False

    def _count_team(self, room_id: str, team: str) -> int:
        count = 0
        for i in range(len(self.players)):
            p = self.players[i]
            key = f"{room_id}:{p.address}"
            if self._key_in_log(key) and p.team == team:
                count += 1
        return count

    def _generate_room_code(self) -> str:
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = ""
        seed = int(self.room_counter) + 1000
        for _ in range(6):
            code += chars[seed % len(chars)]
            seed = seed // len(chars) + int(self.room_counter) + 1
        return code


