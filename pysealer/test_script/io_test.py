"""Testing IO Utilities.

Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

import os
import pysealer as ps
from pysealer import sealer

app_path = os.path.join(ps.HOME_PATH, "Documents", "workspace", "test_app")

seal_app = sealer.Sealer(app_path, host_platform="osx",
                         target_platform="osx", pyver=2)

seal_app.init_build()
seal_app.config_environment()
seal_app.compile_app()
seal_app.prepare_app()
seal_app.seal_app()
seal_app.makeself(os.path.join(os.environ["HOME"], "makeself", "makeself.sh"))
