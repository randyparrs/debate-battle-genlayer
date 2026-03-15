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
