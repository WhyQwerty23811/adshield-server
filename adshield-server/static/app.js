// AdShield VPS Web Dashboard Logic

let currentStatusFilter = 'all';
let allLogs = [];
let serverHostname = 'dns.example.com';

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLogs();
    fetchRules();

    // Auto-refresh loops
    setInterval(fetchStats, 2500);
    setInterval(fetchLogs, 2500);
});

// Tab Navigation
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.add('active');

    const clickedBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b =>
        b.getAttribute('onclick').includes(tabId)
    );
    if (clickedBtn) clickedBtn.classList.add('active');
}

// Fetch Real-time Stats
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        if (!res.ok) return;
        const data = await res.json();

        // Update Hostname
        if (data.server_hostname) {
            serverHostname = data.server_hostname;
            document.getElementById('modalHostnameDisplay').value = serverHostname;
            document.getElementById('guideAndroidHost').innerText = serverHostname;
            document.getElementById('guideDohUrl').innerText = `https://${serverHostname}/dns-query`;
        }

        // Metrics
        const s = data.stats || {};
        document.getElementById('valTotalQueries').innerText = (s.total_queries || 0).toLocaleString();
        document.getElementById('valBlockedQueries').innerText = (s.blocked_queries || 0).toLocaleString();
        document.getElementById('valBlockRate').innerText = `${s.block_rate_pct || 0}%`;
        document.getElementById('ratioBarFill').style.width = `${Math.min(100, s.block_rate_pct || 0)}%`;
        document.getElementById('valUptime').innerText = `Uptime: ${data.uptime || '0m'}`;
        document.getElementById('valCommunityRules').innerText = `${(s.community_rules_count || 0).toLocaleString()} Active Rules`;

        // Cache Stats
        const c = data.cache || {};
        document.getElementById('valCacheRate').innerText = `${c.hit_rate_pct || 0}%`;
        document.getElementById('valCacheCount').innerText = `${(c.hits || 0).toLocaleString()} queries served from RAM`;

        // Shields Counters
        document.getElementById('valYtBlocked').innerText = `Blocked: ${(s.youtube_blocked || 0).toLocaleString()} ads`;
        document.getElementById('valSpBlocked').innerText = `Blocked: ${(s.spotify_blocked || 0).toLocaleString()} ads`;
        document.getElementById('valHsBlocked').innerText = `Blocked: ${(s.hotstar_blocked || 0).toLocaleString()} ads`;

        // Toggles
        if (data.shields) {
            document.getElementById('toggleYouTube').checked = !!data.shields.youtube_shield;
            document.getElementById('toggleSpotify').checked = !!data.shields.spotify_shield;
            document.getElementById('toggleHotstar').checked = !!data.shields.hotstar_shield;
        }

        // Upstream radio
        if (data.upstream_provider) {
            const radio = document.querySelector(`input[name="upstreamProvider"][value="${data.upstream_provider}"]`);
            if (radio) radio.checked = true;
        }

    } catch (err) {
        console.error('fetchStats error:', err);
    }
}

// Fetch Query Logs
async function fetchLogs() {
    try {
        const res = await fetch('/api/logs');
        if (!res.ok) return;
        const data = await res.json();
        allLogs = data.logs || [];
        renderLogsTable();
    } catch (err) {
        console.error('fetchLogs error:', err);
    }
}

function renderLogsTable() {
    const tbody = document.getElementById('queryTableBody');
    const searchTerm = document.getElementById('querySearchInput').value.trim().toLowerCase();

    const filtered = allLogs.filter(entry => {
        // Status filter
        if (currentStatusFilter === 'blocked' && entry.status !== 'blocked') return false;
        if (currentStatusFilter === 'allowed' && entry.status !== 'allowed' && entry.status !== 'forwarded') return false;
        if (currentStatusFilter === 'cached' && entry.status !== 'cached') return false;

        // Search term
        if (searchTerm) {
            const matchDomain = (entry.domain || '').toLowerCase().includes(searchTerm);
            const matchIp = (entry.client_ip || '').toLowerCase().includes(searchTerm);
            return matchDomain || matchIp;
        }
        return true;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 24px;">No matching DNS queries found.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.slice(0, 100).map(entry => {
        let badgeClass = 'badge-allowed';
        let statusText = 'ALLOWED';
        if (entry.status === 'blocked') {
            badgeClass = 'badge-blocked';
            statusText = 'BLOCKED';
        } else if (entry.status === 'cached') {
            badgeClass = 'badge-cached';
            statusText = 'CACHED';
        }

        return `
            <tr>
                <td style="color: var(--text-muted);">${entry.timestamp}</td>
                <td><span style="color: var(--cyan); font-weight: 600;">${entry.protocol}</span></td>
                <td style="color: var(--text-secondary);">${entry.client_ip}</td>
                <td style="font-weight: 600; color: #fff;">${escapeHtml(entry.domain)}</td>
                <td><span style="color: var(--purple);">${entry.qtype}</span></td>
                <td><span class="badge-status ${badgeClass}">${statusText}</span></td>
                <td style="color: var(--green);">${entry.latency_ms} ms</td>
            </tr>
        `;
    }).join('');
}

function setQueryStatusFilter(status, btnElement) {
    currentStatusFilter = status;
    document.querySelectorAll('.filter-chips .chip').forEach(el => el.classList.remove('active'));
    btnElement.classList.add('active');
    renderLogsTable();
}

function filterQueriesTable() {
    renderLogsTable();
}

// Shields Toggle
async function toggleShield(shieldName, isEnabled) {
    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [shieldName]: isEnabled })
        });
        if (res.ok) {
            showToast(`Updated ${shieldName.replace('_', ' ')}: ${isEnabled ? 'ENABLED' : 'DISABLED'}`);
        }
    } catch (err) {
        showToast('Error updating shield');
    }
}

// Change Upstream
async function changeUpstream(provider) {
    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ upstream_provider: provider })
        });
        if (res.ok) {
            showToast(`Upstream resolver updated to ${provider}`);
        }
    } catch (err) {
        showToast('Error changing upstream');
    }
}

// Rules Management
async function fetchRules() {
    try {
        const res = await fetch('/api/rules');
        if (!res.ok) return;
        const data = await res.json();

        // Whitelist
        const wl = data.whitelist || [];
        document.getElementById('whitelistCount').innerText = wl.length;
        document.getElementById('whitelistItems').innerHTML = wl.map(d => `
            <li>
                <span>${escapeHtml(d)}</span>
                <button onclick="removeRule('whitelist', '${escapeHtml(d)}')">✕</button>
            </li>
        `).join('') || '<li class="text-muted text-sm">No custom whitelisted domains.</li>';

        // Blacklist
        const bl = data.blacklist || [];
        document.getElementById('blacklistCount').innerText = bl.length;
        document.getElementById('blacklistItems').innerHTML = bl.map(d => `
            <li>
                <span>${escapeHtml(d)}</span>
                <button onclick="removeRule('blacklist', '${escapeHtml(d)}')">✕</button>
            </li>
        `).join('') || '<li class="text-muted text-sm">No custom blacklisted domains.</li>';

    } catch (err) {
        console.error('fetchRules error:', err);
    }
}

async function addRule(type) {
    const input = document.getElementById(type === 'whitelist' ? 'addWhitelistInput' : 'addBlacklistInput');
    const domain = input.value.trim();
    if (!domain) return;

    try {
        const res = await fetch('/api/rules/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, domain })
        });
        if (res.ok) {
            input.value = '';
            showToast(`Added ${domain} to ${type}`);
            fetchRules();
        }
    } catch (err) {
        showToast('Failed to add rule');
    }
}

async function removeRule(type, domain) {
    try {
        const res = await fetch('/api/rules/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, domain })
        });
        if (res.ok) {
            showToast(`Removed ${domain}`);
            fetchRules();
        }
    } catch (err) {
        showToast('Failed to remove rule');
    }
}

async function updateCommunityList() {
    showToast('Downloading latest StevenBlack hosts...');
    try {
        const res = await fetch('/api/update-blocklists', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'Blocklist update completed!');
        fetchStats();
    } catch (err) {
        showToast('Failed to update community list');
    }
}

// Modal Controls
function openModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.add('active');
}

function closeModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.remove('active');
}

function copyHostname() {
    const input = document.getElementById('modalHostnameDisplay');
    input.select();
    navigator.clipboard.writeText(input.value);
    showToast('Hostname copied to clipboard!');
}

// Toast
function showToast(msg) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.classList.add('show');
    setTimeout(() => {
        t.classList.remove('show');
    }, 3200);
}

function escapeHtml(str) {
    return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

