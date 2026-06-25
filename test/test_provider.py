"""Tests for the YouTube Music MediaProvider plugin (network-free)."""
from unittest.mock import MagicMock, patch

from mediavocab import MediaType, Release, Signals, Work

from ovos_media_provider_youtube_music import YouTubeMusicMediaProvider


def _make_release(title="Some Song"):
    work = Work(title=title, media_type=MediaType.MUSIC)
    return Release(work=work, uri="https://music.youtube.com/watch?v=abc",
                   platform="youtube_music")


def test_instantiation():
    provider = YouTubeMusicMediaProvider()
    assert provider.name == "youtube_music"


def test_search_empty_title_returns_empty():
    provider = YouTubeMusicMediaProvider()
    assert provider.search(Signals(title="")) == []
    assert provider.search(Signals()) == []


def test_search_wires_to_tutubo_bridge():
    """search() drives tutubo.YoutubeMusicSearch and maps each MusicTrack
    through the bridge into a mediavocab.Release."""
    provider = YouTubeMusicMediaProvider()

    track = MagicMock()
    fake_work = Work(title="Paranoid", media_type=MediaType.MUSIC)

    fake_search = MagicMock()
    fake_search.iterate_tracks.return_value = iter([track])

    with patch("tutubo.YoutubeMusicSearch", return_value=fake_search) as ctor, \
            patch("tutubo.mediavocab_bridge.music_track_to_work",
                  return_value=fake_work) as to_work, \
            patch("tutubo.mediavocab_bridge.music_track_to_release",
                  return_value=_make_release("Paranoid")) as to_release:
        results = provider.search(
            Signals(title="black sabbath paranoid"),
            lang="en-us",
            supported_playback_types={"audio"},
            blocked_genres={"adult"},
            region="US",
            session_id="sess-1",
        )

    ctor.assert_called_once_with("black sabbath paranoid")
    fake_search.iterate_tracks.assert_called_once()
    to_work.assert_called_once_with(track)
    to_release.assert_called_once_with(track, fake_work)

    assert isinstance(results, list)
    assert len(results) == 1
    assert all(isinstance(r, Release) for r in results)
    assert results[0].work.title == "Paranoid"


def test_search_swallows_per_item_errors():
    provider = YouTubeMusicMediaProvider()

    bad = MagicMock()
    good = MagicMock()

    fake_search = MagicMock()
    fake_search.iterate_tracks.return_value = iter([bad, good])

    def _to_work(track):
        if track is bad:
            raise RuntimeError("boom")
        return Work(title="ok", media_type=MediaType.MUSIC)

    with patch("tutubo.YoutubeMusicSearch", return_value=fake_search), \
            patch("tutubo.mediavocab_bridge.music_track_to_work",
                  side_effect=_to_work), \
            patch("tutubo.mediavocab_bridge.music_track_to_release",
                  return_value=_make_release("ok")):
        results = provider.search(Signals(title="anything"))

    assert [r.work.title for r in results] == ["ok"]
