#!/usr/bin/env python3
"""Optional axe-core WCAG 2 A/AA + 2.1 AA audit, desktop and mobile.

Pass a local copy of axe.min.js; the production website never loads this library:
    python3 tests/accessibility_test.py /path/to/axe.min.js

Automated checks complement, but do not replace, keyboard and screen-reader review.
"""
import argparse
import json
from pathlib import Path
from site_test import BASE, ROOT, make_driver


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('axe', type=Path, help='Local axe-core JavaScript file')
    args = parser.parse_args()
    source = args.axe.read_text()
    driver = make_driver()
    driver.set_script_timeout(45)
    failures = []
    scans = 0
    try:
        driver.execute_cdp_cmd('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-reduced-motion', 'value': 'reduce'}]})
        for width in [1440, 390]:
            driver.set_window_size(width, 1100)
            for page in sorted(ROOT.glob('*.html')):
                driver.get(BASE + page.name)
                if page.stem in ['cart', 'checkout']:
                    driver.execute_script("window.JoziCart.clear(); window.JoziCart.add({sku:'wilds',size:'500g',grind:'Whole bean',qty:2});")
                driver.execute_script(source)
                result = driver.execute_async_script("""
                    var done = arguments[0];
                    axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}},
                      function(error, result){done(error ? {error:String(error)} : result);});
                """)
                scans += 1
                violations = result.get('violations', [])
                if result.get('error') or violations:
                    failures.append({'page': page.name, 'width': width, 'error': result.get('error'),
                                     'violations': [{'id': v['id'], 'impact': v['impact'], 'nodes': [n['target'] for n in v['nodes']]} for v in violations]})
                print(('FAIL ' if violations or result.get('error') else 'PASS ') + f'{page.name} / {width}px')
    finally:
        driver.quit()
    print(f'\n{scans-len(failures)}/{scans} automated accessibility scans passed.')
    if failures:
        print(json.dumps(failures, indent=2))
        raise SystemExit(1)
