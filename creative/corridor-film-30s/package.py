from pathlib import Path
import zipfile
R=Path(__file__).resolve().parent
with zipfile.ZipFile(R/'AtlasIQ-30s-editable-project.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in R.rglob('*'):
  if p.is_file() and p.suffix not in ['.zip','.pyc','.log'] and '__pycache__' not in str(p) and not p.name.startswith('voice-test'):
   z.write(p,Path('AtlasIQ-30s')/p.relative_to(R))
print(R/'AtlasIQ-30s-editable-project.zip')
