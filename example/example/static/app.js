const hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🩷", "🤍", "🖤"];
let idx = 0;

document.addEventListener("mousemove", (e) => {
  const el = document.createElement("span");
  el.className = "heart";
  el.textContent = hearts[idx++ % hearts.length];
  el.style.left = e.clientX + "px";
  el.style.top = e.clientY + "px";
  document.body.appendChild(el);
  el.addEventListener("animationend", () => el.remove());
});
