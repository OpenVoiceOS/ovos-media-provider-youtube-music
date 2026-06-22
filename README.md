# ovos-media-provider-youtube-music

OVOS **MediaProvider** plugin for YouTube Music. Replaces the deprecated OCP
search skill [`ovos-skill-youtube-music`](https://github.com/OpenVoiceOS/ovos-skill-youtube-music).

Instead of broadcasting `ovos.common_play.query` over the bus and waiting for
skills to answer, the OCP pipeline loads MediaProvider plugins in-process, gates
them by routing, and calls `search()` directly. This plugin wraps the
[`tutubo`](https://github.com/TigreGotico/tutubo) YouTube Music client
(`tutubo.ytmus` / `ytmusicapi`), whose `MusicTrack` results convert to
[`mediavocab.Release`](https://github.com/TigreGotico/mediavocab) objects via
tutubo's `mediavocab_bridge`.

## Install

```bash
pip install ovos-media-provider-youtube-music
```

## Routing

| Axis | Value |
|------|-------|
| `media` | `MUSIC`, `MUSIC_VIDEO` |
| `playback_type` | `AUDIO` |
| `genre_filter` | *(none)* |

## Entry point

```toml
[project.entry-points."opm.media.provider"]
youtube_music = "ovos_media_provider_youtube_music:YouTubeMusicMediaProvider"
```

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `max_results` | `10` | Maximum number of results returned per search. |

## License

Apache-2.0
