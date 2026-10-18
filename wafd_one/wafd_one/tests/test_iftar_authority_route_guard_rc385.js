/** Regression test for the real global mobile-navigation bundle, without Frappe server. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = path.resolve(__dirname, '..', '..');
const files = [
  path.join(ROOT, 'public', 'wafd_mobile_navigation.bundle.js'),
  path.join(ROOT, 'public', 'js', 'wafd_mobile_navigation.js'),
];

function launch(file, roles, start='wafd-role-home', shape='simple') {
  let current = start;
  let routeChange;
  const redirects = [];
  const body = {classList: {toggle() {}}, appendChild() {}, prepend() {}};
  const document = {
    readyState: 'complete', body,
    querySelectorAll: () => [],
    getElementById: id => id === 'wafd-field-appbar-rc278' ? {remove() {}} : null,
    createElement: tag => ({tagName: tag, style: {}, classList: {toggle() {}},
      setAttribute() {}, appendChild() {}, addEventListener() {}, querySelector() {return null;}}),
    addEventListener() {},
  };
  const frappe = {
    session: {user: 'external-viewer-test@example.test'}, user_roles: roles,
    get_route: () => shape === 'page' ? ['Page', current] : [current],
    set_route: route => {redirects.push(route); current = route;},
    router: {on: (event, fn) => {if (event === 'change') routeChange = fn;}},
  };
  const window = {
    frappe, location: {pathname: '/app/' + current, replace: url => redirects.push('REPLACE ' + url)},
    matchMedia: () => ({matches: true}), screen: {width: 390},
    addEventListener() {}, getComputedStyle: () => ({display: 'block', visibility: 'visible'}),
  };
  const context = {window, document, frappe, navigator: {userAgent: 'iPhone', maxTouchPoints: 5},
    MutationObserver: class {observe() {}}, requestAnimationFrame: fn => fn(),
    setTimeout() {}, console};
  vm.runInNewContext(fs.readFileSync(file, 'utf8'), context, {filename: file, timeout: 1500});
  return {
    redirects,
    navigate(route) {
      current = route;
      window.location.pathname = '/app/' + route;
      routeChange();
    },
  };
}

for (const file of files) {
  for (const shape of ['simple', 'page']) {
    const authority = launch(file, ['WAFD Iftar Authority Viewer'], 'wafd-role-home', shape);
    assert.deepEqual(authority.redirects, [], 'home is accessible');
    // Simulate report popup closing, then home, then opening the authority viewer
    // repeatedly. The route guard must not intercept the viewer's own route.
    for (let i = 0; i < 5; i++) {
      authority.navigate('wafd-iftar-authority-viewer');
      assert.deepEqual(authority.redirects, [], `viewer entry #${i+1} must not redirect`);
      authority.navigate('wafd-role-home');
      assert.deepEqual(authority.redirects, [], `home return #${i+1} must not redirect`);
    }
    const forbidden = launch(file, ['WAFD Iftar Authority Viewer'], 'wafd-iftar-site', shape);
    assert.deepEqual(forbidden.redirects, ['wafd-role-home'], 'authority user cannot open site management');
    const driver = launch(file, ['WAFD Driver'], 'wafd-iftar-authority-viewer', shape);
    assert.deepEqual(driver.redirects, ['wafd-role-home'], 'driver cannot open authority monitoring');
    const delivery = launch(file, ['WAFD Delivery Viewer'], 'wafd-iftar-authority-viewer', shape);
    assert.deepEqual(delivery.redirects, ['wafd-role-home'], 'delivery viewer cannot open authority monitoring');
    const dual = launch(file, ['WAFD Delivery Viewer', 'WAFD Iftar Authority Viewer'], 'wafd-iftar-authority-viewer', shape);
    assert.deepEqual(dual.redirects, [], 'explicitly dual-assigned field viewer may open authority monitoring');
  }
  // Initial fresh browser document: Frappe route is not yet initialized.
  const src = fs.readFileSync(file, 'utf8');
  assert.match(src, /pathIsRoute\(IFTAR_AUTHORITY_VIEWER_ROUTE\)/);
  console.log('PASS', path.relative(ROOT, file), 're-entry, role isolation, Page routes');
}
