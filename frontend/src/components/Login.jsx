import { useState } from "react";
import { login } from "../api.js";

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      const token = await login(username, password);
      onLogin(token);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="login-box">
      <h1>Systematic Investing Platform</h1>
      <form onSubmit={handleSubmit}>
        <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input placeholder="Password" type="password" value={password}
               onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">Log in</button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}

export default Login;
