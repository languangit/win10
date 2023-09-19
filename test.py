import tools
import os

print(f"tools---->{tools.get_base_path()}")
print(f"本地---->{os.path.dirname(os.path.abspath(__file__))}")
