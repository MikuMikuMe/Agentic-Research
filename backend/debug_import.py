import sys
import os
sys.path.append(os.getcwd())

print("Current cwd:", os.getcwd())
print("Sys path:", sys.path)

try:
    import app
    print("App package:", app)
    import app.agents
    print("App.agents package:", app.agents)
    import app.agents.tools as tools
    print("Tools module:", tools)
    print("Attributes in tools:", dir(tools))
    
    from app.agents.tools import search_arxiv
    print("Imported search_arxiv:", search_arxiv)
    
except Exception as e:
    print("Caught Exception:", e)
    import traceback
    traceback.print_exc()
