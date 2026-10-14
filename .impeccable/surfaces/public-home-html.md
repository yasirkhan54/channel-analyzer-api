---
version: 1
slug: "public-home-html"
primary_target: "public/home.html"
related_targets: ["public/assets/docs.css"]
---

# Home page and API docs header

Scope: the public home page (`/`) and the Swagger UI info section above the API list (`/api-docs`). Mode: Operate and Read (the owner checks status, finds an endpoint, learns the quota rules). Pinned by the user: youtube.com is the visual reference. Product rules: no YouTube logos or brand assets, no em dashes.

Assumptions taken without asking (owner prefers build over questions): system light/dark preference with a toggle on the home page; Swagger stays light; Roboto stands in for YouTube Sans.

## Direction contract

THESIS: The API presents itself as a channel on the site it analyses. Refuses the developer-landing default of hero, stat tiles and icon cards.

OWN-WORLD: youtube.com grammar. #0F0F0F / #FFFFFF grounds, #272727 / #F2F2F2 chips, one red (#FF0033) used only for live state and time progress, with one cited exception: the tallest bar of the brand mark (the mark reads as a quota meter), pill buttons in text colour, 12px thumbnails, Roboto, masthead with search, left guide.

STORY: The owner sees the service is online, how much of today's quota day is left, what gets stored, finds any endpoint from the masthead search, and copies the key header.

FIRST VIEWPORT: Masthead (mark, search that filters endpoints, status, Docs pill). Left guide. Channel header: quota-day strip banner with red now marker, avatar mark, name, meta line, description, pills, tabs. Below: watch layout, live health response as the player with the red quota-day progress bar, Up next queue of the four fetch steps on the right.

FORM: Video platform channel and watch page, user-pinned (no concept roll: a pinned brief beats the roll). Seed key: pinned-youtube-reference.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
