// Point this to your deployed backend:
const API = "https://music-app-dqaf.onrender.com";
const API_URL = "https://music-app-dqaf.onrender.com";

// Helpers
const $ = (sel) => document.querySelector(sel);
const player = $("#player");

async function getJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Load playlists into UI
async function loadPlaylists() {
  const data = await getJSON(`${API}/playlists`);

  // Fill the select used by "Add Track"
  const select = $("#playlistSelect");
  select.innerHTML = "";
  data.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name;
    select.appendChild(opt);
  });

  // Render cards
  const container = $("#playlists");
  container.innerHTML = "";
  data.forEach(p => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h3>${p.name} <span class="badge">${p.tracks.length} tracks</span></h3>
      <div class="tracks"></div>
    `;
    const tracksDiv = card.querySelector(".tracks");
    p.tracks.forEach(t => {
      const row = document.createElement("div");
      row.className = "track";
      row.innerHTML = `
        <img src="${t.album_cover || ""}" alt="">
        <div style="flex:1">
          <div><strong>${t.title}</strong></div>
          <div>${t.artist}</div>
        </div>
        <button>▶</button>
      `;
      row.querySelector("button").onclick = () => play(t.preview);
      tracksDiv.appendChild(row);
    });
    container.appendChild(card);
  });
}

// Playback
function play(url) {
  if (!url) {
    alert("No preview URL for this track.");
    return;
  }
  player.src = url;
  player.play();
}

// Create playlist
async function createPlaylist() {
  const name = $("#playlistName").value.trim();
  if (!name) return alert("Enter a playlist name.");
  await getJSON(`${API}/playlists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  $("#playlistName").value = "";
  await loadPlaylists();
}

// Add track
async function addTrack() {
  const playlist_id = Number($("#playlistSelect").value);
  const title = $("#title").value.trim();
  const artist = $("#artist").value.trim();
  const preview = $("#preview").value.trim();
  const album_cover = $("#cover").value.trim();
  const track_id = $("#trackId").value.trim() || crypto.randomUUID();

  if (!playlist_id || !title || !artist) {
    return alert("Playlist, title, and artist are required.");
    }

  await getJSON(`${API}/playlists/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ playlist_id, track_id, title, artist, preview, album_cover })
  });

  // Clear inputs (keep playlist selection)
  ["title","artist","preview","cover","trackId"].forEach(id => $("#"+id).value = "");
  await loadPlaylists();
}

// Wire up events
$("#createBtn").onclick = createPlaylist;
$("#addTrackBtn").onclick = addTrack;

// Initial fetch
loadPlaylists().catch(err => alert("Failed to load playlists: " + err.message));
