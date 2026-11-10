# KETTENREAKTION – Übergabe für neue Sessions

> **Fester Nutzerwunsch (wie bei ZahlenBlitz):** Nach jedem fertigen Video **ohne Nachfrage** eine Download-Seite veröffentlichen
> (Artifact mit den MP4s als `files`, `capabilities: {"downloads": true}`, icon "video") und den Link nennen.

Download-Seite: https://claude.ai/artifact/DRZ7x4oYYwuk4JdKZvTs3W (Quelle `downloads.html`, neue Folge oben einfügen, MP4 über `files`).

## Aufbau
- `kr.py`: Engine. Stimme (ElevenLabs + Cache), Timing, T+-Pille und Kette, Karaoke-Untertitel, Übergänge, Bloom/Grain/Vignette/Tonemapping,
  Hilfsfunktionen (`sphere()` für beleuchtete Planeten mit Wolken/Stadtlichtern/Atmosphäre, `fnoise`, `starfield`, `splat` für Partikel, `text_fx` mit Glow),
  prozedurale Musik (Drohnen-Pad je Segment, Ticken als Puls der Zeitleiste, Whoosh, Boom, Ketten-„Klink“, Riser vor dem Twist), 4 Render-Prozesse, 2-Pass auf −14 LUFS.
- `videos/<thema>/<thema>.py`: ein Video. Enthält `SEGS`, `SCENES` (Hintergrund als float-Array HxWx3), `overlay()` (Text/Grafik auf dem PIL-Bild),
  `CHORDS`, `SOURCES`, `MAX_LEN`, am Ende `kr.run(globals())`.
- SEGS-Felder: `say` (Sprechtext, Zahlen als Wörter), `min` (Mindestdauer), `stamp` (Text in der T+-Pille), `node` (Kettenglied),
  `twist`, `nosub`, `noui`, `nosrc`, `shake`.

## Neues Video
1. `videos/mond/` nach `videos/<thema>/` kopieren und `voice_cache/` löschen.
2. SEGS und die Szenen umschreiben (Hook, 4 Glieder, Twist, Outro).
3. Vorschau, 0 Credits: `python3 <thema>.py out/x.mp4 --preview 0 2 6 …` → `out/pv_*.png` ansehen.
4. Stimme: `KR_VOICE=1 python3 <thema>.py out/x.mp4 --preview 1` (holt nur fehlende Abschnitte, die Proxy-Injektion liefert den Key).
5. Rendern: `python3 <thema>.py out/kettenreaktion_NN_<thema>.mp4` (~3 min).
6. Web-/Upload-Version < 15 MB: 2-Pass x264 mit `-preset slow -b:v 2650k` (bei 41 s → 14,6 MB).

## ElevenLabs
voice_id **`ML23UVoFL5mI6APbRAeR`** ab Video #02 (Nutzerwunsch). #01 Mond nutzt weiter `TUKJhQmz3RPYBNAgC5A1` (Override `VOICE_ID` in mond.py), damit sein Cache gültig bleibt, eleven_multilingual_v2, Settings wie in `kr.py`. Ohne `KR_VOICE=1` wird nie vertont.

## Videos
| # | Ordner | Thema | Länge |
|---|---|---|---|
| 01 | videos/mond | Was wäre, wenn der Mond verschwindet? | 41 s |
| 02 | videos/stopp | Was wäre, wenn die Erde aufhört, sich zu drehen? | 38 s |
| 03 | videos/insekten | Was wäre, wenn alle Insekten verschwinden? | 44 s |
| 04 | videos/sonne | Was wäre, wenn die Sonne ausgeht? | 38 s |
| 05 | videos/eis | Was wäre, wenn alles Eis der Erde schmilzt? (Pille zeigt +Meter statt T+) | 37 s |
| 06 | videos/loch | Was wäre, wenn du in ein Schwarzes Loch fällst? (Gravitationslinse in loch.py) | 35 s |

Gemeinsame Bausteine stehen in `lib.py` (Erde/Mond/Sonne, Sterne, `heads()`, `hook_text()`, `outro()`, Emoji, Kreuz).
Fertigstellen: `tools/finish.sh <ordner> <nr> <Titel>` (Stimme holen, rendern, Web-Version < 15 MB, Lautheit auf −14 korrigieren).
Download-Seite: mehr als 64 MB pro Publish geht nicht, also MP4s auf mehrere Publishes an dieselbe URL verteilen.
