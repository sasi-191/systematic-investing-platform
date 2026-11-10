const API_URL = "http://localhost:8000";

export async function login(username, password) {
  // FastAPI's login route expects form data, not JSON
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  const response = await fetch(API_URL + "/login", { method: "POST", body: form });
  if (!response.ok) {
    throw new Error("Wrong username or password");
  }
  const data = await response.json();
  return data.access_token;
}

export async function getData(path, token) {
  const response = await fetch(API_URL + path, {
    headers: { Authorization: "Bearer " + token },
  });
  if (response.status === 401) {
    throw new Error("LOGIN_AGAIN");
  }
  return response.json();
}

export async function postJson(path, token, body) {
  const response = await fetch(API_URL + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
    body: JSON.stringify(body),
  });
  return response.json();
}

export async function postData(path, token) {
  const response = await fetch(API_URL + path, {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
  });
  return response.json();
}
