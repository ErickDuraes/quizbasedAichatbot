// Save username in localStorage
function saveUser(username) {
  localStorage.setItem("username", username);
}

function getUser() {
  return localStorage.getItem("username") || "";
}

// Redirect helpers
function goTo(page) {
  window.location.href = page;
}
