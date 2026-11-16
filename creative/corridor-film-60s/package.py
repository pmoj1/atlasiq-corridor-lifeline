from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
R=Path(__file__).resolve().parent
with ZipFile(R/'AtlasIQ-60s-editable-project.zip','w',ZIP_DEFLATED,compresslevel=5) as z:
 for p in sorted(R.rglob('*')):
  if p.is_file() and p.suffix not in ['.zip','.pyc','.log'] and '__pycache__' not in p.parts:
   z.write(p,Path('AtlasIQ-60s')/p.relative_to(R))
print('Packaged editable project, media, prompts and verification')
