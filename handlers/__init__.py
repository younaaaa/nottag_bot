from .music import setup_music_handlers
from .general_handlers import setup_general_handlers
from .batch_handlers import setup_batch_handlers # Added
# Import other handler setup functions here if you create more files

def setup_handlers(application):
    """Registers all application command and message handlers."""
    setup_music_handlers(application)
    setup_general_handlers(application)
    setup_batch_handlers(application) # Added
    # Call other setup functions
    print("All handlers configured.")
