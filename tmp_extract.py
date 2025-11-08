from zipfile import ZipFile
from pathlib import Path
from bs4 import BeautifulSoup
zip_path=Path('RawOCW/18.01sc-fall-2010.zip')
with ZipFile(zip_path) as zf:
    html = zf.read('pages/unit-3-the-definite-integral-and-its-applications/part-a-definition-of-the-definite-integral-and-first-fundamental-theorem/session-45-some-easy-integrals/index.html').decode('utf-8', errors='ignore')
soup = BeautifulSoup(html, 'html.parser')
h1 = soup.find('h1')
print('h1:', h1.get_text(strip=True) if h1 else None)
print('breadcrumbs:', [li.get_text(strip=True) for li in soup.select('nav.breadcrumbs li')])
print('unit title:', soup.select_one('[data-testid="CourseUnitSection-title"]'))
print('page title node:', soup.select_one('[data-testid="CourseSectionHeader-title"]'))
