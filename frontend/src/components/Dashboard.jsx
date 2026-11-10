import { useEffect, useState } from "react";
import { getData, postData, postJson } from "../api.js";
import DataTable from "./DataTable.jsx";
import Performance from "./Performance.jsx";

function Dashboard({ token, onLogout }) {
  const [summary, setSummary] = useState(null);
  const [positions, setPositions] = useState([]);
  const [orders, setOrders] = useState({ done: [], waiting_for_tomorrow: [] });
  const [trades, setTrades] = useState([]);
  const [signals, setSignals] = useState([]);
  const [performance, setPerformance] = useState({ chart: [], months: [] });
  const [fyers, setFyers] = useState({ configured: false, logged_in_today: false, live_trading_enabled: false });
  const [livePrices, setLivePrices] = useState(false);
  const [message, setMessage] = useState("");

  async function loadEverything() {
    try {
      setSummary(await getData("/summary", token));
      setPositions(await getData("/positions?live=" + livePrices, token));
      setOrders(await getData("/orders", token));
      setTrades(await getData("/trades", token));
      setSignals(await getData("/signals", token));
      setPerformance(await getData("/performance", token));
      setFyers(await getData("/fyers/status", token));
    } catch (err) {
      if (err.message === "LOGIN_AGAIN") {
        onLogout();
      }
    }
  }

  // load the data when the page opens
  useEffect(() => {
    loadEverything();
  }, []);

  // with live prices on, refresh the positions every 5 seconds
  useEffect(() => {
    if (!livePrices) {
      return;
    }
    async function refreshPositions() {
      setPositions(await getData("/positions?live=true", token));
    }
    refreshPositions();
    const timer = setInterval(refreshPositions, 5000);
    return () => clearInterval(timer);
  }, [livePrices]);

  async function runJob() {
    setMessage("Running... the first run downloads a year of prices and takes a few minutes.");
    const result = await postData("/run-daily-job", token);
    setMessage(result.message || result.action);
    loadEverything();
  }

  async function loginToFyers() {
    const answer = await getData("/fyers/login-url", token);
    if (answer.url) {
      window.location.href = answer.url;      // Fyers sends us back to the dashboard after login
    } else {
      setMessage(answer.detail);
    }
  }

  async function placeLiveOrders() {
    const typed = window.prompt("This sends REAL orders to Fyers. Type CONFIRM to continue.");
    if (typed === null) {
      return;
    }
    const answer = await postJson("/live/place-orders", token, { confirm: typed });
    setMessage(answer.results.join(" | "));
  }

  if (!summary) {
    return <p>Loading...</p>;
  }

  let totalProfit = 0;
  for (const position of positions) {
    totalProfit = totalProfit + position.profit;
  }

  return (
    <div className="page">
      <header>
        <h1>Systematic Investing Platform</h1>
        <button onClick={onLogout}>Log out</button>
      </header>

      <div className="cards">
        <div className="card">Account value<b>Rs {summary.total_value}</b></div>
        <div className="card">Profit<b>{summary.profit_percent} %</b></div>
        <div className="card">Cash<b>Rs {summary.cash}</b></div>
        <div className="card">Last run<b>{summary.last_run || "never"}</b></div>
      </div>

      <div className="toolbar">
        <button onClick={runJob}>Run today's job</button>
        {fyers.logged_in_today ? (
          <span className="ok">Fyers: logged in</span>
        ) : (
          <button onClick={loginToFyers}>Login to Fyers</button>
        )}
        <label>
          <input type="checkbox" checked={livePrices} onChange={(e) => setLivePrices(e.target.checked)} />
          Live prices {summary.market_open ? "(market open)" : "(market closed)"}
        </label>
        {fyers.live_trading_enabled && (
          <button className="danger" onClick={placeLiveOrders}>Place today's orders (REAL)</button>
        )}
      </div>
      {message && <p>{message}</p>}

      <h2>Stocks we hold</h2>
      <p>Profit on open positions: <b>Rs {totalProfit.toFixed(2)}</b></p>
      <DataTable rows={positions} columns={[
        { key: "symbol", title: "Stock" }, { key: "shares", title: "Shares" },
        { key: "buy_price", title: "Buy price" }, { key: "price", title: "Price now" },
        { key: "profit", title: "Profit (Rs)" }, { key: "profit_percent", title: "Profit %" },
      ]} />

      <h2>Performance</h2>
      <Performance data={performance} />

      <h2>Orders for tomorrow</h2>
      <DataTable rows={orders.waiting_for_tomorrow} columns={[
        { key: "symbol", title: "Stock" }, { key: "side", title: "Buy or sell" }, { key: "reason", title: "Why" },
      ]} />

      <h2>Top 10 stocks today</h2>
      <DataTable rows={signals} columns={[
        { key: "rank", title: "Rank" }, { key: "symbol", title: "Stock" },
        { key: "return_6_months_percent", title: "6 month return %" },
      ]} />

      <h2>Finished trades</h2>
      <DataTable rows={trades} columns={[
        { key: "symbol", title: "Stock" }, { key: "buy_date", title: "Bought" },
        { key: "sell_date", title: "Sold" }, { key: "profit", title: "Profit (Rs)" },
      ]} />

      <h2>Order history</h2>
      <DataTable rows={orders.done} columns={[
        { key: "date", title: "Date" }, { key: "symbol", title: "Stock" }, { key: "side", title: "Side" },
        { key: "shares", title: "Shares" }, { key: "price", title: "Price" }, { key: "reason", title: "Why" },
      ]} />
    </div>
  );
}

export default Dashboard;
