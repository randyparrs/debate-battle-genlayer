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
