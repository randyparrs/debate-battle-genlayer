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
