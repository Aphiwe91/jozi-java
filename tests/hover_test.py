#!/usr/bin/env python3
"""Pointer, keyboard, reduced-motion and touch checks for the interaction layer.

Uses a real desktop pointer rather than Chromium's headless hover:none default.
On headless Linux: xvfb-run -a python3 tests/hover_test.py
Requires the usual :8002 preview server; no new website runtime dependencies.
"""
import unittest

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from site_test import BASE, make_driver


class HoverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver(headless=False)
        cls.driver.execute_cdp_cmd('DOM.enable', {})
        cls.driver.execute_cdp_cmd('CSS.enable', {})

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        self.driver.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride', {})
        self.driver.execute_cdp_cmd('Emulation.setTouchEmulationEnabled', {'enabled': False})
        self.motion('no-preference')
        self.driver.set_window_size(1440, 1050)
        self.open('index.html')

    def motion(self, value):
        self.driver.execute_cdp_cmd('Emulation.setEmulatedMedia', {
            'features': [{'name': 'prefers-reduced-motion', 'value': value}]
        })

    def open(self, page):
        self.driver.get(BASE + page)
        WebDriverWait(self.driver, 8).until(lambda d: d.execute_script('return !!window.JoziCart;'))
        self.driver.execute_script('document.documentElement.style.scrollBehavior="auto";')

    def element(self, selector):
        return self.driver.find_element('css selector', selector)

    def style(self, selector, property, pseudo=None):
        return self.driver.execute_script('return getComputedStyle(arguments[0],arguments[2]).getPropertyValue(arguments[1]);', self.element(selector), property, pseudo)

    def hover(self, selector, enabled=True):
        root = self.driver.execute_cdp_cmd('DOM.getDocument', {})['root']['nodeId']
        node = self.driver.execute_cdp_cmd('DOM.querySelector', {'nodeId': root, 'selector': selector})['nodeId']
        self.driver.execute_cdp_cmd('CSS.forcePseudoState', {
            'nodeId': node, 'forcedPseudoClasses': ['hover'] if enabled else []
        })
        self.driver.execute_script('''
            void arguments[0].offsetWidth;
            arguments[0].getAnimations({subtree:true}).forEach(function (animation) {
                if (animation.effect.getComputedTiming().iterations !== Infinity) animation.finish();
            });
        ''', self.element(selector))

    def keyboard_focus(self, selector):
        self.element('body').send_keys(Keys.TAB)
        self.driver.execute_script('''
            arguments[0].focus({preventScroll:true});
            void arguments[0].offsetWidth;
            document.getAnimations().forEach(function (animation) {
                if (animation.effect.getComputedTiming().iterations !== Infinity) animation.finish();
            });
        ''', self.element(selector))
        self.assertTrue(self.driver.execute_script('return arguments[0].matches(":focus-visible");', self.element(selector)))

    def test_desktop_hover_lifts_buttons_and_cards(self):
        self.assertTrue(self.driver.execute_script('return matchMedia("(hover:hover) and (pointer:fine)").matches;'))
        ActionChains(self.driver).move_to_element(self.element('.jj-service-card')).perform()
        WebDriverWait(self.driver, 4).until(lambda d: self.style('.jj-service-card', 'transform') != 'none')
        self.assertTrue(self.driver.execute_script('return arguments[0].matches(":hover");', self.element('.jj-service-card')))
        self.assertIn('0.25s', self.style('.jj-service-card', 'transition-duration'))
        ActionChains(self.driver).move_to_element(self.element('.jj-chat')).perform()
        for selector in ('.jj-service-card', '.jj-featured-equipment > article', '.jj-home-coffee > article', '.jj-hero-welcome .btn-primary', '.jj-chat'):
            with self.subTest(selector=selector):
                self.hover(selector)
                self.assertNotEqual(self.style(selector, 'transform'), 'none')
                self.assertNotEqual(self.style(selector, 'box-shadow'), 'none')
                self.hover(selector, False)
        self.open('shop.html')
        self.hover('.jj-card')
        self.assertNotEqual(self.style('.jj-card', 'transform'), 'none')
        self.assertNotEqual(self.style('.jj-card .jj-product-image img', 'transform'), 'none')

    def test_image_zoom_is_clipped_and_keeps_layout_stable(self):
        for parent, image in (('.jj-tile', '.jj-tile > img.is-active'), ('.jj-editorial-card', '.jj-editorial-card img'), ('.jj-home-gallery > a', '.jj-home-gallery img'), ('.jj-photo-mosaic > a', '.jj-photo-mosaic img')):
            with self.subTest(parent=parent):
                before = self.driver.execute_script('return [arguments[0].offsetWidth,arguments[0].offsetHeight];', self.element(parent))
                self.hover(parent)
                self.assertNotEqual(self.style(image, 'transform'), 'none')
                after = self.driver.execute_script('return [arguments[0].offsetWidth,arguments[0].offsetHeight];', self.element(parent))
                self.assertEqual(before, after)
                self.assertTrue(self.driver.execute_script('return document.documentElement.scrollWidth<=document.documentElement.clientWidth+1;'))
                self.hover(parent, False)
        self.assertEqual(self.style('.jj-hero-background', 'transform'), 'none')
        self.assertEqual(self.style('.jj-hero-background', 'opacity'), '0.6')

    def test_keyboard_gets_visible_equivalent_feedback(self):
        self.motion('reduce')
        self.keyboard_focus('.jj-service-card')
        self.assertEqual(self.style('.jj-service-card', 'outline-style'), 'solid')
        self.assertEqual(self.style('.jj-service-card', 'outline-width'), '3px')
        self.assertNotEqual(self.style('.jj-service-card', 'box-shadow'), 'none')
        self.assertEqual(self.style('.jj-service-card', 'transform'), 'none')
        self.keyboard_focus('#ftco-nav a[href="equipment.html"]')
        self.assertEqual(self.style('#ftco-nav a[href="equipment.html"]', 'transform', '::after'), 'matrix(1, 0, 0, 1, 0, 0)')
        self.open('shop.html')
        self.keyboard_focus('.jj-card h3 a')
        self.assertNotEqual(self.style('.jj-card', 'box-shadow'), 'none')

    def test_reduced_motion_keeps_feedback_without_movement(self):
        self.motion('reduce')
        for selector in ('.jj-service-card', '.jj-hero-welcome .btn-primary', '.jj-chat'):
            with self.subTest(selector=selector):
                self.hover(selector)
                self.assertEqual(self.style(selector, 'transform'), 'none')
                self.assertEqual(self.style(selector, 'transition-duration'), '0s')
                self.hover(selector, False)
        self.hover('.jj-tile')
        self.assertEqual(self.style('.jj-tile > img.is-active', 'transform'), 'none')
        self.hover('.jj-service-card')
        self.assertEqual(self.style('.jj-service-card', 'background-color'), 'rgb(242, 245, 235)')

    def test_touch_keeps_actions_visible_without_hover_motion(self):
        self.driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
        self.driver.execute_cdp_cmd('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 1})
        self.open('index.html')
        self.assertTrue(self.driver.execute_script('return matchMedia("(hover:none)").matches;'))
        self.hover('.jj-service-card')
        self.assertEqual(self.style('.jj-service-card', 'transform'), 'none')
        self.hover('.jj-tile')
        self.assertEqual(self.style('.jj-tile > img.is-active', 'transform'), 'none')
        self.assertTrue(all(button.is_displayed() for button in self.driver.find_elements('css selector', '.jj-hero-welcome .jj-actions a')))
        self.open('shop.html')
        buttons = self.driver.find_elements('css selector', '.jj-add')
        self.assertEqual(len(buttons), 3)
        self.assertTrue(all(button.is_displayed() for button in buttons))

    def test_equipment_rows_highlight_without_becoming_fake_links(self):
        self.open('equipment.html')
        self.hover('#casadio-2')
        self.assertEqual(self.style('#casadio-2', 'background-color'), 'rgb(237, 242, 230)')
        self.assertEqual(self.style('#casadio-2', 'transform'), 'none')
        self.hover('#casadio-2', False)
        self.keyboard_focus('#casadio-2 .btn')
        self.assertEqual(self.style('#casadio-2', 'background-color'), 'rgb(237, 242, 230)')


if __name__ == '__main__':
    unittest.main(verbosity=2)
