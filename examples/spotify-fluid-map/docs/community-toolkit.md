# Spotify Fluid Map Community Toolkit

This folder tracks third-party TouchDesigner tools that are worth auditioning for Spotify Fluid Map. The public repo stores the manifest, downloader, and notes; actual `.tox`, `.toe`, zip, and cloned third-party files go into ignored runtime storage.

```bash
python3 examples/spotify-fluid-map/scripts/fetch_community_toolkit.py --list
python3 examples/spotify-fluid-map/scripts/fetch_community_toolkit.py
```

Default downloads land in:

```text
examples/spotify-fluid-map/runtime/community/
```

Use `--all` for optional local-only candidates such as GPL VJ control surfaces, and `--force` to refresh an existing local copy.

## First Audition Order

1. **TD-Toxes Performance Pack**: start with `abstractFluid_MYLES.tox`, `pixelSorting_MYLES.tox`, `reactionDiffusion_MYLES.tox`, and `dataMosh_MYLES.tox`. These were created in TD `2023.11600`, so they are the closest match to this machine.
2. **13 Tap Bloom**: audition as a replacement or parallel branch for the current bloom/sharpen lane. Drive bloom strength from kick and high-band energy.
3. **RayTK 0.37**: import into a blank project first, then create one small raymarched scene driven by `low`, `mid`, `high`, and track-change pulses.
4. **ISF parser + VIDVOX ISF files**: load one shader at a time and wire Spotify/audio channels into exposed uniforms.
5. **MaxMainio TD_ sparse subset**: use edge detectors, mapping, SDF, texture synthesis, and sorting components to derive masks from album art.
6. **Dominant Color**: use as a reference for stronger album-art palette extraction. Its dependency notes are older, so avoid making it live-critical until tested.

## Visual Integration Ideas

- Album art enters the patch as the stable visual seed.
- MusicBrainz enrichment adds optional genre/tag strings and MBIDs.
- The bridge's deterministic title/artist/album hashes choose effect families.
- Low band controls displacement, scale, and RayTK camera travel.
- Mid band controls palette rotation, ISF parameter morphing, and feedback angle.
- High band controls bloom, edge sharpness, and particle/spark density.
- Kick pulses trigger flash, RayTK object swaps, or datamosh freezes.
- Snare pulses trigger edge-map inversion, shader threshold changes, or pixel sorting.
- Track-change pulses reseed palette, scene family, ISF shader choice, and feedback memory.

## Metadata Enrichment

Spotify's newer app restrictions mean this example should not depend on Spotify Audio Features or Audio Analysis. For V1, use:

- Spotify Desktop AppleScript for now-playing metadata.
- live audio capture into TouchDesigner for energy, bands, kick, and snare.
- optional MusicBrainz lookup for recording MBID, release MBID, artist MBIDs, tags, and genres.

Run the optional enrichment helper after the bridge is writing `now_playing.json`:

```bash
python3 examples/spotify-fluid-map/scripts/enrich_now_playing_musicbrainz.py
```

It writes:

```text
examples/spotify-fluid-map/runtime/song_enrichment.json
```

For a long-running helper:

```bash
python3 examples/spotify-fluid-map/scripts/enrich_now_playing_musicbrainz.py --watch --poll-ms 5000
```

MusicBrainz requires a meaningful user agent and no more than one request per second. The helper caches results by title, artist, and album.

## Mapping Candidates

Derivative's built-in mapping tools remain the primary show path:

- Kantan Mapper for 2D projection shapes and masks.
- CamSchnappr for physical 3D structures with a virtual model.
- Projector Blend for multi-projector arrays.
- Stoner for manual image/mesh warping.
- Quad Reproject and Corner Pin TOP/SOP for fixed pixel/layout outputs.

The templates in `community/mapping_templates/` are source-readable starting points for future mapper automation. They are not yet imported by the TD builder.

## Intake Rules

- Treat every `.tox` and `.toe` as executable.
- Open each candidate in a blank TouchDesigner project first.
- Record operator errors, warnings, FPS, external files, Python usage, networking usage, and TD version.
- Keep GPL or unclear-license assets local unless the project intentionally adopts compatible license terms.
- Do not commit downloaded third-party binaries without a license note and smoke-test record.
