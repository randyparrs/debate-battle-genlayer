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

        calle
