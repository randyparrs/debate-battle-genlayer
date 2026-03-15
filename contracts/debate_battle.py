# contracts/debate_battle.py
# Debate Battle — GenLayer Intelligent Contract
# Mini-game for GenLayer Community

from genlayer import IContract, public
from genlayer.py.types import Address
import json
import random


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

    def __init__(self):
        self.rooms: dict[str, dict] = {}
        self.room_counter: int = 0
        self.player_xp: dict[str, int] = {}

    @public
    def create_room(self, time_limit_minutes: int) -> str:
        assert time_limit_minutes in [5, 10, 15], "Time limit must be 5, 10, or 15 minutes"

        room_id = self._generate_room_code()
        caller = str(self.contract_runner.from_address)

        topic_index = self.room_counter % len(WEEKLY_TOPICS)
        topic = WEEKLY_TOPICS[topic_index]

        self.rooms[room_id] = {
            "host": caller,
            "topic": topic,
            "topic_index": topic_index,
            "time_limit": time_limit_minutes,
            "players": {},
            "team_a_players": [],
            "team_b_players": [],
            "status": "waiting",
            "winner_team": None,
            "best_argument_player": None,
            "judgment_reasoning": None,
            "created_at": self.room_counter,
        }

        self.room_counter += 1
        return room_id

    @public
    def join_room(self, room_id: str) -> str:
        assert room_id in self.rooms, "Room not found"
        room = self.rooms[room_id]
        assert room["status"] == "waiting", "Room is no longer accepting players"
        assert len(room["players"]) < 8, "Room is full (max 8 players)"

        caller = str(self.contract_runner.from_address)
        assert caller not in room["players"], "You have already joined this room"

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
        assert room_id in self.rooms, "Room not found"
        room = self.rooms[room_id]
        caller = str(self.contract_runner.from_address)

        assert caller in room["players"] or caller == room["host"], "You are not in this room"
        assert room["status"] == "arguing", "Debate is not in arguing phase"

        room["status"] = "judging"

        search_query = room["topic"].replace(" ", "+")
        context_url = f"https://en.wikipedia.org/w/index.php?search={search_query}&ns0=1"

        try:
            web_context = get_webpage(context_url, mode="text")
            web_context = web_context[:2000]
        except Exception:
            web_context = "No additional context available. Judge based on argument quality alone."

        team_a_arguments = []
        team_b_arguments = []

        for player_addr, player_data in room["players"].items():
            if player_data["submitted"] and player_data["argument"]:
                entry = f"Player {player_addr[:8]}...: {player_data['argument']}"
                if player_data["team"] == "A":
                    team_a_arguments.append(entry)
                else:
                    team_b_arguments.append(entry)

        assert len(team_a_arguments) > 0 or len(team_b_arguments) > 0, "No arguments submitted yet"

        team_a_text = "\n".join(team_a_arguments) if team_a_arguments else "No arguments submitted"
        team_b_text = "\n".join(team_b_arguments) if team_b_arguments else "No arguments submitted"

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

        for player_addr, player_data in room["players"].items():
            if player_addr not in self.player_xp:
                self.player_xp[player_addr] = 0

            if player_data["team"] == winner_team:
                self.player_xp[player_addr] += 100
            else:
                self.player_xp[player_addr] += 20

        if best_player and best_player in self.player_xp:
            self.player_xp[best_player] += 50

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
        assert room_id in self.rooms, "Room not found"
        return self.rooms[room_id]

    @public
    def get_leaderboard(self) -> list:
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
        return self.player_xp.get(player_address, 0)

    @public
    def get_weekly_topic(self) -> str:
        index = self.room_counter % len(WEEKLY_TOPICS)
        return WEEKLY_TOPICS[index]

    def _generate_room_code(self) -> str:
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = ""
        seed = self.room_counter + 1000
        for _ in range(6):
            code += chars[seed % len(chars)]
            seed = seed // len(chars) + self.room_counter
        return code
