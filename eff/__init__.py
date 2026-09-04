"""EFF — Equipment Fitness Framework.

A scored, auditable answer to "should this machine stay in service?".
"""

__version__ = "1.0.0"

from .models import Asset
from .verdict import Assessment, assess

__all__ = ["Asset", "Assessment", "assess", "__version__"]
