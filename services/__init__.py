from .tag_editor import TagEditorService
from .musicbrainz_service import MusicBrainzService
from .acoustid_service import AcoustIDService
from .genius_service import GeniusService
from .soundcloud_service import SoundCloudService # Added
from .spotify_service import SpotifyService     # Added

__all__ = [
    'TagEditorService',
    'MusicBrainzService',
    'AcoustIDService',
    'GeniusService',
    'SoundCloudService', # Added
    'SpotifyService'     # Added
]
