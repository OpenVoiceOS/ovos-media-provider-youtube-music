"""OVOS MediaProvider plugin for YouTube Music.

Replaces the deprecated OCP search skill ``ovos-skill-youtube-music``. Instead of
answering ``ovos.common_play.query`` over the bus, this provider is loaded
in-process by the OCP pipeline, gated by the three-axis routing test, and its
:meth:`search` is called directly.

All YouTube Music access is delegated to the ``tutubo`` client library. Its
``YoutubeMusicSearch`` (backed by ``tutubo.ytmus`` / ``ytmusicapi``) yields
``MusicTrack`` wrappers, which this provider maps into ``mediavocab.Release``
objects via tutubo's ``mediavocab_bridge`` (``music_track_to_work`` /
``music_track_to_release``).
"""
from typing import List, Optional, Set, ClassVar

from ovos_utils.log import LOG

from mediavocab import MediaType, Release, Signals
from mediavocab.taxonomy import PlaybackType
from ovos_plugin_manager.templates.media_provider import MediaProvider

from ovos_media_provider_youtube_music.version import __version__  # noqa: F401


class YouTubeMusicMediaProvider(MediaProvider):
    """Search YouTube Music and return ``mediavocab.Release`` playables.

    Routing (three-axis gate):

    * ``media`` — ``MUSIC`` and ``MUSIC_VIDEO``.
    * ``playback_type`` — ``AUDIO`` only (YouTube Music tracks are consumed as
      audio streams; the backend selector resolves the stream at playback).
    * ``genre_filter`` — empty (no genre gate).
    """

    name: ClassVar[str] = "youtube_music"

    media: ClassVar[Set[MediaType]] = {
        MediaType.MUSIC,
        MediaType.MUSIC_VIDEO,
    }

    playback_type: ClassVar[Set[PlaybackType]] = {
        PlaybackType.AUDIO,
    }

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        # max results per search, overridable via plugin config
        self.max_results: int = int(self.config.get("max_results", 10))

    def is_available(self) -> bool:
        """``tutubo`` (with ``ytmusicapi``) is a hard dependency and YouTube
        Music needs no API key, so the provider is always available (network
        reachability is handled per-search by the pipeline's ``search_safe``
        wrapper)."""
        return True

    def search(self, signals: Signals, lang: str = "en-us") -> List[Release]:
        """Search YouTube Music for ``signals.title`` and return Releases.

        Delegates to ``tutubo.YoutubeMusicSearch``: each ``MusicTrack`` it
        yields is mapped through tutubo's ``mediavocab_bridge`` into a
        ``mediavocab.Release``.
        """
        query = (signals.title or "").strip()
        if not query:
            return []

        from tutubo import YoutubeMusicSearch
        from tutubo.mediavocab_bridge import (
            music_track_to_work,
            music_track_to_release,
        )

        releases: List[Release] = []
        try:
            search = YoutubeMusicSearch(query)
            for track in search.iterate_tracks(max_res=self.max_results):
                try:
                    work = music_track_to_work(track)
                    releases.append(music_track_to_release(track, work))
                except Exception:
                    LOG.exception("Failed to convert YouTube Music result to Release")
        except Exception:
            LOG.exception(f"YouTube Music search failed for query: {query!r}")
        return releases
