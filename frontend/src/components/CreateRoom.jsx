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
