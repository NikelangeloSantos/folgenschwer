# FOLGENSCHWER – Übergabe für neue Sessions

> **Fester Nutzerwunsch (wie bei ZahlenBlitz):** Nach jedem fertigen Video **ohne Nachfrage** eine Download-Seite veröffentlichen
> (Artifact mit den MP4s als `files`, `capabilities: {"downloads": true}`, icon "video") und den Link nennen.

GitHub: https://github.com/NikelangeloSantos/folgenschwer (lokal oft noch unter /home/user/kettenreaktion geklont).
Download-Seite: https://claude.ai/artifact/DRZ7x4oYYwuk4JdKZvTs3W (Quelle `downloads.html`, neue Folge oben einfügen, MP4 über `files`).

## Aufbau
- `kr.py`: Engine. Stimme (ElevenLabs + Cache), Timing, Zeit-Pille („NACH …“, Präfix automatisch bei Zahlen und „MIO.“) und Kette, Karaoke-Untertitel, Übergänge, Bloom/Grain/Vignette/Tonemapping,
  Hilfsfunktionen (`sphere()` für beleuchtete Planeten mit Wolken/Stadtlichtern/Atmosphäre, `fnoise`, `starfield`, `splat` für Partikel, `text_fx` mit Glow),
  prozedurale Musik (Drohnen-Pad je Segment, Ticken als Puls der Zeitleiste, Whoosh, Boom, Ketten-„Klink“, Riser vor dem Twist), 4 Render-Prozesse, 2-Pass auf −14 LUFS.
- `videos/<thema>/<thema>.py`: ein Video. Enthält `SEGS`, `SCENES` (Hintergrund als float-Array HxWx3), `overlay()` (Text/Grafik auf dem PIL-Bild),
  `CHORDS`, `SOURCES`, `MAX_LEN`, am Ende `kr.run(globals())`.
- SEGS-Felder: `say` (Sprechtext, Zahlen als Wörter), `min` (Mindestdauer), `stamp` (Text in der Zeit-Pille; Grammatik beachten: „6 MONATEN“, „MIO. JAHREN“; Hook: „JETZT“), `node` (Kettenglied),
  `twist`, `nosub`, `noui`, `nosrc`, `shake`.

## Neues Video
1. `videos/mond/` nach `videos/<thema>/` kopieren und `voice_cache/` löschen.
2. SEGS und die Szenen umschreiben (Hook, 4 Glieder, Twist, Outro).
3. Vorschau, 0 Credits: `python3 <thema>.py out/x.mp4 --preview 0 2 6 …` → `out/pv_*.png` ansehen.
4. Stimme: `KR_VOICE=1 python3 <thema>.py out/x.mp4 --preview 1` (holt nur fehlende Abschnitte, die Proxy-Injektion liefert den Key).
5. Rendern: `python3 <thema>.py out/folgenschwer_NN_<thema>.mp4` (~3 min).
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
| 05 | videos/eis | Was wäre, wenn alles Eis der Erde schmilzt? (Pille zeigt +Meter statt Zeit) | 37 s |
| 06 | videos/loch | Was wäre, wenn du in ein Schwarzes Loch fällst? (Gravitationslinse in loch.py) | 35 s |

Gemeinsame Bausteine stehen in `lib.py` (Erde/Mond/Sonne, Sterne, `heads()`, `hook_text()`, `outro()`, Emoji, Kreuz).
Fertigstellen: `tools/finish.sh <ordner> <nr> <Titel>` (Stimme holen, rendern, Web-Version < 15 MB, Lautheit auf −14 korrigieren).
Download-Seite: mehr als 64 MB pro Publish geht nicht, also MP4s auf mehrere Publishes an dieselbe URL verteilen.
| 07 | videos/tunnel | Was wäre, wenn du durch die Erde fällst? | |
| 08 | videos/springen | Was wäre, wenn alle Menschen gleichzeitig springen? | |
| 09 | videos/kaugummi | Was wäre, wenn du einen Kaugummi verschluckst? | |
| 10 | videos/schlaf | Was wäre, wenn du nie wieder schläfst? | |
| 11 | videos/euro | Was wäre, wenn du jeden Tag 1 € sparst? | |

Mehrere Videos am Stück: `tools/batch.sh "ordner NN Titel" "ordner NN Titel" …`
Themenmix (Nutzerwunsch): auch banale/unrealistische Alltagsfragen („hat sich jeder schon mal gefragt“), nicht nur Natur/Weltall.
| 12 | videos/gesetze | Was wäre, wenn es ab morgen keine Gesetze mehr gäbe? (MUSTER neuer Hook) | 42,5 s |

## Hook-Regeln ab #12 (aus YouTube-Auswertung #10: 58,5 % Sehdauer gut, aber ~75 % wischen sofort weg)
- Stimme beginnt mit der krassesten Folge/Zahl, Frage erst danach; Hook ≤ ~3,5 s.
- Frame 0 schon in Bewegung (Push-in, Licht-Wechsel, Shake), kein ruhiges Standbild.
- Im Hook nur 2–3 riesige Wörter, kein „WAS WÄRE, WENN“-Kicker.
- Outro-Frage themenbezogen („Welches Gesetz würdest du …?“) + passenden Kommentar anpinnen.

## 3D-Doodle-Stil (ab #12, Nutzerwunsch: „krasser, keine langen Standbilder, 3D Doodle“)
- `doodle.py`: Layer mit Kamera (Zoom/Pan/Rotation), Line-Boil 12 fps, extrudierte Formen (`poly`, `box`, `circ`), 3D-Text (`text`),
  Figuren `bean()` (Bohnen mit Augen), `car()`, `flame()`, `bill()`, `burst()`, `scribbles()` (Hintergrund-Gekritzel). Zeichnet 2× und skaliert runter.
- Pro Kettenglied 2–3 Beats (`beat(rel, [0, 1.8, 3.6])`) mit Zoom-Punch, Kamera immer in Bewegung (`cam()`), knallige Verläufe statt Weltall-Navy.
- Vorlage: `videos/gesetze/gesetze.py` (flache Vorversion: `gesetze_v1_flat.py`). Render ~7 min.
