"""Copy the static dashboard to GitHub Pages' /docs publication directory."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
target=root/'docs';target.mkdir(exist_ok=True)
for path in (root/'dist').iterdir():
 if path.is_file():shutil.copyfile(path,target/path.name)
(target/'.nojekyll').write_text('',encoding='utf8')
print('GitHub Pages: docs atualizado.')
