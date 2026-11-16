"""Regression check for the maintainer's edit-once workflow. Requires D2 0.9.0."""
from pathlib import Path
import base64
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'


def render(root, view, output):
    # Zero disables D2's default deadline. Leave errors visible in CI.
    subprocess.run(['d2', '--layout', 'elk', '--timeout', '0',
                    str(root / 'views' / (view + '.d2')), str(output)],
                   check=True)
    svg = ET.parse(output).getroot()
    labels = {''.join(e.itertext()) for e in svg.iter(NS + 'text')}
    links = {e.get('href') or e.get('{http://www.w3.org/1999/xlink}href')
             for e in svg.iter(NS + 'a')}
    return labels, links



def rendered_connections(output, classes=None):
    """Read D2's rendered edge IDs, normalizing their common path prefix."""
    edges = set()
    for group in ET.parse(output).getroot().iter(NS + 'g'):
        if classes and not classes.intersection(group.get('class', '').split()):
            continue
        if not any('connection' in p.get('class', '').split()
                   for p in group.findall(NS + 'path')):
            continue
        for token in group.get('class', '').split():
            try:
                key = base64.b64decode(token, validate=True).decode()
            except (ValueError, UnicodeDecodeError):
                continue
            match = re.fullmatch(r'(?:(.*?)\.)?\((.*?) -- (.*?)\)\[\d+\]', key)
            if match:
                prefix, source, target = match.groups()
                prefix = prefix + '.' if prefix else ''
                if (prefix + source).split('.')[0] in {'rnas', 'server', 'mechanical', 'facility_network'}:
                    edges.add(frozenset([prefix + source, prefix + target]))
    return edges

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


    def test_dense_labels_preserve_devices_wiring_and_explicit_captions(self):
        def snapshot(output):
            objects, edges = {}, {}
            for group in ET.parse(output).getroot().iter(NS + 'g'):
                tokens = group.get('class', '').split()
                if not tokens:
                    continue
                try:
                    key = base64.b64decode(tokens[0], validate=True).decode()
                except (ValueError, UnicodeDecodeError):
                    continue
                if not key.startswith(('rnas', 'server', 'mechanical', 'facility_network')):
                    continue
                labels = tuple(''.join(t.itertext()) for t in group.iter(NS + 'text'))
                if any('connection' in p.get('class', '').split()
                       for p in group.findall(NS + 'path')):
                    edges[key] = (tuple(tokens[1:]), labels)
                else:
                    objects[key] = labels
            return objects, edges

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'arch'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'svg', '__pycache__'))
            compact = Path(temp) / 'compact.svg'
            labels, _ = render(root, 'zimager_connections', compact)
            compact_objects, compact_edges = snapshot(compact)
            view = root / 'views/zimager_connections.d2'
            view.write_text(view.read_text().replace('(** -- **)[*]: {!&label: *; label: ""}\n', '')
                            .replace('(** -> **)[*]: {!&label: *; label: ""}\n', ''))
            original = Path(temp) / 'original.svg'
            render(root, 'zimager_connections', original)
            original_objects, original_edges = snapshot(original)
            self.assertEqual(compact_objects, original_objects)
            self.assertEqual(compact_edges.keys(), original_edges.keys())
            self.assertGreater(len(compact_edges), 50)
            generic = {'AC', 'DC', 'Ethernet', 'EtherCAT', 'USB', 'Motor / position',
                       'CXP ×4', 'CXP fiber', 'Air', 'Glycol S/R', 'I/O'}
            cleared = 0
            for key, (classes, before) in original_edges.items():
                after_classes, after = compact_edges[key]
                self.assertEqual(classes, after_classes, key)
                if after != before:
                    self.assertEqual(after, (), key)
                    self.assertTrue(set(before).issubset(generic), (key, before))
                    cleared += 1
            self.assertGreater(cleared, 30)
            for caption in ['100 Mb/s copper', '24 VDC', '12 VDC', '1-Wire']:
                self.assertTrue(any(caption in texts for _, texts in compact_edges.values()), caption)
            self.assertIn('Motor / position', labels)  # Native legend remains labeled.

    def test_power_sources_reach_every_distribution_through_supplies(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'power.svg'
            render(ROOT, 'zshooter_power', output)
            edges = rendered_connections(output)
            front = 'rnas.zshooter.zfront.ebox.'
            imager = 'rnas.zshooter.zimager.ebox.'
            vis = 'rnas.zshooter.zspec_vis.ebox.'
            nir = 'rnas.zshooter.zspec_nir.ebox.'
            incoming = ['rnas.ac_feed', 'rnas.panel',
                        front + 'facility_panel', front + 'ac']
            vis_path = incoming + [front + 'panels.vis_panel', vis + 'input_panel',
                                   vis + 'power_bus', vis + 'dc', vis + 'dc_distribution']
            paths = [incoming + [front + 'dc', front + 'dc_distribution'],
                     incoming + [front + 'panels.imager_panel', imager + 'input_panel',
                                 imager + 'power_bus', imager + 'dc', imager + 'dc_distribution'],
                     vis_path,
                     vis_path + [vis + 'panels.nir_panel', nir + 'input_panel', nir + 'power_bus']]
            for path in paths:
                path.append(path[-1].rsplit('.', 1)[0] + '.computer')
                for source, target in zip(path, path[1:]):
                    self.assertIn(frozenset([source, target]), edges, (source, target))
            for prefix in [front, imager, vis]:
                ups = prefix + 'dc_ups'
                incident = [edge for edge in edges if ups in edge]
                self.assertEqual(incident, [frozenset([ups, prefix + 'dc_distribution'])])
            self.assertFalse(any(nir + 'dc_ups' in edge for edge in edges))

    def test_power_includes_all_supply_paths_and_new_loads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'arch'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'svg', '__pycache__'))
            model = root / 'model/zimager.d2'
            with model.open('a') as f:
                f.write('\nzimager.ebox.dc_distribution -- zimager.enclosure.added_load: {class: dc}\n')
            complete, power = Path(temp) / 'complete.svg', Path(temp) / 'power.svg'
            render(root, 'zshooter_connections', complete)
            render(root, 'zshooter_power', power)
            supply_classes = {'power', 'dc', 'motion', 'detector', 'carries_power'}
            expected = rendered_connections(complete, supply_classes)
            self.assertGreater(len(expected), 150)
            self.assertEqual(rendered_connections(power), expected)
            self.assertIn(frozenset(['rnas.zshooter.zimager.ebox.dc_distribution',
                                     'rnas.zshooter.zimager.enclosure.added_load']), expected)

    def test_smart_distribution_is_on_each_local_ethernet_switch(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'ethernet.svg'
            render(ROOT, 'zshooter_ethernet', output)
            edges = rendered_connections(output)
            for assembly in ['zfront', 'zimager', 'zspec_vis']:
                prefix = f'rnas.zshooter.{assembly}.ebox.'
                self.assertIn(frozenset([prefix + 'network_switch', prefix + 'dc_distribution']), edges)

    def test_overview_follows_shared_names_and_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'arch'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'svg', '__pycache__'))
            front = root / 'model/zfront.d2'
            front.write_text(front.read_text().replace('label: "ZFront"', 'label: "Front renamed for check"')
                             .replace('link: "../../controls/harnesses/zfront.html"',
                                      'link: "https://example.invalid/front"'))
            server = root / 'model/server.d2'
            server.write_text(server.read_text().replace('label: "NAS / NFS"', 'label: "Storage renamed for check"'))
            optics = root / 'model/optical_paths.d2'
            optics.write_text(optics.read_text().replace('label: "Left Neighbor"', 'label: "Neighbor renamed for check"'))
            labels, links = render(root, 'zshooter_overview', Path(temp) / 'overview.svg')
            for label in ['Front renamed for check', 'Storage renamed for check', 'Neighbor renamed for check']:
                self.assertIn(label, labels)
            self.assertIn('https://example.invalid/front', links)
            for old in ['ZFront', 'NAS / NFS', 'Left Neighbor']:
                self.assertNotIn(old, labels)


if __name__ == '__main__':
    unittest.main()
