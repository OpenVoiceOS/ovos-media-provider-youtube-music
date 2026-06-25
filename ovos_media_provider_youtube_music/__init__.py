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
from typing import ClassVar, List, Optional, Set

from ovos_utils.log import LOG

from mediavocab import Release, Signals
from ovos_plugin_manager.templates.media_provider import MediaProvider

from ovos_media_provider_youtube_music.version import __version__  # noqa: F401


class YouTubeMusicMediaProvider(MediaProvider):
    """Search YouTube Music and return ``mediavocab.Release`` playables."""

    name: ClassVar[str] = "youtube_music"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        # max results per search, overridable via plugin config
        self.max_results: int = int(self.config.get("max_results", 10))

    def search(self, signals: Signals, lang: str = "en-us", *,
               supported_playback_types: Optional[Set[str]] = None,
               blocked_genres: Optional[Set[str]] = None,
               region: Optional[str] = None,
               session_id: Optional[str] = None) -> List[Release]:
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
