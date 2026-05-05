import os
import glob
import shutil

# Caminhos
docs_dir = "docs"
state_dir = os.path.join("state", "seen")

print("Limpando arquivos XML em docs/...")
for f in glob.glob(os.path.join(docs_dir, "*.xml")):
    try:
        os.remove(f)
        print(f"  Removido: {f}")
    except: pass

print("Limpando memória de duplicados em state/seen/...")
for f in glob.glob(os.path.join(state_dir, "*.json")):
    try:
        os.remove(f)
        print(f"  Removido: {f}")
    except: pass

print("Iniciando reconstrução total dos feeds...")
os.system("python engine/run.py")
