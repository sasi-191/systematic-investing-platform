import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import DataTable from "./DataTable.jsx";

// Our account value next to Nifty, both starting at the same amount, and the return of each month
function Performance({ data }) {
  if (data.chart.length === 0) {
    return <p className="empty">The chart appears after the first daily job.</p>;
  }

  return (
    <div>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.chart}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" minTickGap={40} />
            <YAxis domain={["auto", "auto"]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="account" name="Our account (Rs)" stroke="#1f6feb" dot={false} />
            <Line type="monotone" dataKey="nifty" name="Nifty 50 (same start)" stroke="#999999" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h3>Return of each month</h3>
      <DataTable rows={data.months} columns={[
        { key: "month", title: "Month" }, { key: "return_percent", title: "Return %" },
      ]} />
    </div>
  );
}

export default Performance;
