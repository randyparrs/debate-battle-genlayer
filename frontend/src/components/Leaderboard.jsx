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
