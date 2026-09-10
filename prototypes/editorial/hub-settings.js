// Public, reviewed configuration only. Never store API keys here.
window.HUB_SETTINGS = {
  live: {
    // Confirmed current broadcast: { platform: 'twitch', title, checkedAt, expiresAt }.
    // Expired confirmations are never displayed as live.
    broadcast: null,
    // Confirmed schedule: { platform: 'twitch', title, startsAt: ISO timestamp with offset }.
    next: null,
    youtubeVideoId: null,
    // Confirmed events: { id, platform, titlePT, titleEN, startsAt: ISO timestamp with offset }.
    events: []
  },
  // Only approved, verified, active links: { titlePT, titleEN, url, status: 'active' }.
  affiliates: []
};
