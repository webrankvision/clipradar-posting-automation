"""
Metadata strategy banks — CLIPRADAR METADATA ENGINE v1.0
All hook/CTA/bridge/hashtag/first-comment content pools.
Claude draws from these as style references (not verbatim copies).
"""

# ── HOOK BANKS ────────────────────────────────────────────────────────────────

HOOKS_CONTRARIAN = [
    "This isn't for everyone. Most people will scroll past this.",
    "Nobody talks about this because it ruins the narrative.",
    "You weren't supposed to see this clip.",
    "Delete this before your competition finds it.",
    "The algorithm is going to bury this one.",
    "I almost didn't post this.",
]

HOOKS_CURIOSITY_GAP = [
    "He said one line that changed how I make money online.",
    "This is the part they cut from the interview.",
    "Watch till the end — the last 5 seconds hit different.",
    "3 words. That's all it took.",
    "I've watched this 47 times. It hits harder every time.",
]

HOOKS_IDENTITY = [
    "If you're still working a 9-5 and watching clips like this at 2am — this is your sign.",
    "You're either building something or building someone else's dream.",
    "The ones who save this are the ones who actually do something about it.",
    "This is for the ones who are tired of being tired.",
    "If this doesn't light a fire in you, nothing will.",
]

HOOKS_SHAREABILITY = [  # Instagram-optimized — designed for DM shares
    "Send this to someone who needs to hear this today.",
    "Tag someone who's about to change their life this year.",
    "You know someone who needed this — send it to them.",
    "This is the sign your friend has been waiting for. Share it.",
    "Screenshot this or send it to yourself. You'll need it later.",
]

HOOKS_SEO = [  # YouTube-optimized — keyword-front-loaded for search
    "Faceless Content Strategy That Actually Works",
    "Make Money Clipping Podcasts — The Method No One Shares",
    "How Faceless Creators Build Income With Short Form Content",
    "Podcast Clips to Income — The System",
    "Stop Editing Random Content — Do This Instead",
    "Faceless YouTube Shorts Strategy 2026",
]

HOOK_STYLES = ["contrarian", "curiosity_gap", "identity", "shareability", "seo_keyword"]

HOOK_BANKS = {
    "contrarian": HOOKS_CONTRARIAN,
    "curiosity_gap": HOOKS_CURIOSITY_GAP,
    "identity": HOOKS_IDENTITY,
    "shareability": HOOKS_SHAREABILITY,
    "seo_keyword": HOOKS_SEO,
}

# ── EMOTIONAL BRIDGE LINES ────────────────────────────────────────────────────

BRIDGES = [
    "There's a system that turns clips like this into income. Most people don't know it exists.",
    "What if the content you're watching right now could become your business?",
    "The creators making money from this aren't smarter. They just found the system.",
    "Watching motivational clips feels good. Using them to build income feels better.",
    "You don't need to create content. You need to clip the right content.",
]

BRIDGES_INSTAGRAM = [
    "I created a free system that shows you exactly how to turn clips like this into real income — no face, no followers needed.",
    "There's a method behind this. And I'm giving it away for free to people who are serious.",
    "The creators winning right now found a system. I packaged it. It's yours if you want it.",
]

BRIDGES_FACEBOOK = [
    "6 months ago I was scrolling Facebook at 2am watching clips exactly like this one. Feeling stuck. Feeling like everyone else had it figured out. Then I found a system that turned these same clips into actual income. No face. No following. Just a method. That system is free if you want it.",
    "Everyone says 'just start creating content.' Nobody tells you WHAT content to create. Or how to find the moments worth clipping. Or how to stop wasting hours editing clips that get 47 views. The difference isn't talent. It's source material.",
]

# ── CTA LINES ─────────────────────────────────────────────────────────────────

CTAS_TIKTOK = [
    "DM me SYSTEM and I'll send you the free guide that explains everything.",
    "Send me SYSTEM in my DMs — I built something for people exactly like you.",
    "DM me the word SYSTEM if you want the method. It's free.",
    "SYSTEM ← send me that word in a DM. I'll send you the playbook.",
    "Send SYSTEM to my DMs. I'll reply with something that'll change how you think about content.",
]

CTAS_INSTAGRAM = [
    "Comment SYSTEM and I'll DM you the free guide. No catch.",
    "Type SYSTEM below. I'll send you the exact method.",
    "Want in? Comment SYSTEM — I'll send it directly to your DMs.",
    "One word: SYSTEM. Drop it below and check your DMs.",
    "Comment SYSTEM if you're ready. I'll send you the free playbook.",
]

# Facebook CTAs — no automation, use direct link. Encourage 5+ word responses (weighted 3x by FB algorithm)
CTAS_FACEBOOK = [
    "Get the free guide → https://build2millions.com/ — drop a comment and tell me what part of this hit you hardest.",
    "Full breakdown is free → https://build2millions.com/ — what are you building right now? Tell me below.",
    "Free guide at https://build2millions.com/ — comment what's been holding you back. I read every one.",
    "Grab the free method → https://build2millions.com/ — drop a comment and tell me what clicked for you.",
    "Get it free → https://build2millions.com/ — and tell me: are you still watching or are you building?",
]

# ── FIRST COMMENTS ─────────────────────────────────────────────────────────────
# Auto-posted immediately after publish. Short, personal, reinforce SYSTEM.
# Different from the caption CTA — more conversational.

FIRST_COMMENTS_TIKTOK = [
    "If this hit you — DM me SYSTEM. I'll send you the free guide 👇",
    "The system behind clips like this? Send me SYSTEM in my DMs and I'll send it over.",
    "Want to know how to turn content like this into income? DM me SYSTEM.",
    "SYSTEM ← send me that word in a DM. It unlocks the free method.",
]

FIRST_COMMENTS_INSTAGRAM = [
    "Drop SYSTEM below if you want the free guide sent straight to your DMs 👇",
    "I built something for people who are serious about this. Comment SYSTEM.",
    "Want the method? Just comment SYSTEM. I'll DM you everything.",
    "If this resonated — drop SYSTEM. I'll send you the full system for free.",
]

FIRST_COMMENTS_FACEBOOK = [
    "Free guide if you want the full breakdown → https://build2millions.com/ — drop a comment and tell me what this one unlocked for you 👇",
    "The full method is free at https://build2millions.com/ — let me know in the comments what part hit hardest.",
    "Grab it free → https://build2millions.com/ — and tell me: what are you building right now?",
    "Full breakdown at https://build2millions.com/ — drop a comment and tell me what clicked.",
]

# ── HASHTAG POOLS (3 sets per platform, cycle through them) ───────────────────

HASHTAG_SETS_TIKTOK = [
    ["facelesscontent", "makemoneyonline", "sidehustle", "clipcreator", "podcastclips"],
    ["facelessyoutube", "contentcreator", "passiveincome", "shortformcontent", "motivationclips"],
    ["facelesscreator", "onlineincome", "digitalincome", "workonline", "contentbusiness"],
]

HASHTAG_SETS_INSTAGRAM = [
    ["facelesscontent", "podcastclips", "makemoneyonline", "facelesscreator", "contentclipping"],
    ["shortformcontent", "onlineincome", "sidehustleideas", "clipcreator", "passiveincomeonline"],
    ["facelessyoutube", "contentbusiness", "podcastclips", "makemoneyonline", "reels"],
]

HASHTAG_SETS_YOUTUBE = [
    ["Shorts", "facelesscontent", "makemoneyonline", "podcastclips", "contentcreator"],
    ["Shorts", "facelesscreator", "onlineincome", "shortformcontent", "sidehustle"],
    ["Shorts", "motivation", "facelesscreator", "onlineincome", "shortformcontent"],
]

HASHTAG_SETS_FACEBOOK = [
    ["facelesscontent", "podcastclips", "makemoneyonline"],
    ["motivationalclips", "sidehustle", "contentcreator"],
    ["facelesscreator", "onlineincome", "shortformcontent"],
]
