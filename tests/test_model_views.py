"""Regression check for the maintainer's edit-once workflow. Requires D2 0.9.0."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'


def render(root, view, output):
    subprocess.run(['d2', '--layout', 'elk', '--timeout', '25',
                    str(root / 'views' / (view + '.d2')), str(output)],
                   check=True, capture_output=True, timeout=30)
    svg = ET.parse(output).getroot()
    labels = {''.join(e.itertext()) for e in svg.iter(NS + 'text')}
    links = {e.get('href') or e.get('{http://www.w3.org/1999/xlink}href')
             for e in svg.iter(NS + 'a')}
    return labels, links


@unittest.skipUnless(shutil.which('d2'), 'D2 is required for render regression checks')
class ModelViews(unittest.TestCase):
    def test_filter_change_propagates_to_network_and_connection_views(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'arch'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'svg', '__pycache__'))
            labels, _ = render(root, 'zshooter_usb', Path(temp) / 'before.svg')
            self.assertIn('V filter', labels)
            model = root / 'model' / 'zimager.d2'
            text = model.read_text().replace('interface: usb', 'interface: ethernet')
            text = text.replace('label: "V filter"', 'label: "Filter renamed for regression check"')
            # A link edit in the same source must reach every view containing that object.
            text = text.replace('link: "../../controls/operations/zimager.html"',
                                'link: "https://example.invalid/changed-documentation"')
            model.write_text(text)
            labels, _ = render(root, 'zshooter_usb', Path(temp) / 'usb.svg')
            self.assertNotIn('Filter renamed for regression check', labels)
            self.assertNotIn('V filter', labels)
            for view in ['zshooter_ethernet', 'zimager_connections', 'zshooter_optics']:
                labels, links = render(root, view, Path(temp) / (view + '.svg'))
                self.assertIn('Filter renamed for regression check', labels, view)
                self.assertIn('https://example.invalid/changed-documentation', links, view)
                self.assertNotIn('V filter', labels, view)


if __name__ == '__main__':
    unittest.main()
