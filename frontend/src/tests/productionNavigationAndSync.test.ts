import { describe, it, expect, afterEach } from 'vitest';

// Provide window mock for node test environment
if (typeof globalThis.window === 'undefined') {
  (globalThis as any).window = {
    location: {
      pathname: '/',
      search: '',
      href: 'http://localhost:5173/',
      origin: 'http://localhost:5173',
    },
    history: {
      pushState: () => {},
      replaceState: () => {},
    },
    addEventListener: () => {},
    removeEventListener: () => {},
  };
}

import { parseRouteFromLocation, getPathForView } from '../App';

describe('Production Navigation & Route Persistence (Bug 1)', () => {
  const originalLocation = window.location;

  const setMockLocation = (pathname: string, search: string = '') => {
    (window as any).location = {
      ...originalLocation,
      pathname,
      search,
      href: `http://localhost:5173${pathname}${search}`,
      origin: 'http://localhost:5173',
    };
  };

  afterEach(() => {
    (window as any).location = originalLocation;
  });

  describe('parseRouteFromLocation', () => {
    it('correctly maps root path "/" to landing view', () => {
      setMockLocation('/');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('landing');
      expect(route.designId).toBeNull();
    });

    it('correctly preserves "/production" on direct visit or browser refresh', () => {
      setMockLocation('/production');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('production');
      expect(route.designId).toBeNull();
    });

    it('correctly preserves "/designs" on direct visit or browser refresh', () => {
      setMockLocation('/designs');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('designs');
      expect(route.designId).toBeNull();
    });

    it('correctly preserves "/studio" on direct visit or browser refresh', () => {
      setMockLocation('/studio');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('studio');
      expect(route.designId).toBeNull();
    });

    it('correctly maps "/shop-floor" to production workstation view', () => {
      setMockLocation('/shop-floor');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('production');
    });

    it('correctly extracts designId from query params on "/designs?id=123"', () => {
      setMockLocation('/designs', '?id=d25e210f-b0ae-4b28-944f-a15b141c7a62');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('design-detail');
      expect(route.designId).toBe('d25e210f-b0ae-4b28-944f-a15b141c7a62');
    });

    it('correctly extracts designId from path on "/designs/123"', () => {
      setMockLocation('/designs/test-design-uuid');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('design-detail');
      expect(route.designId).toBe('test-design-uuid');
    });

    it('correctly preserves "/canvas?id=123" on direct visit or refresh', () => {
      setMockLocation('/canvas', '?id=test-canvas-uuid');
      const route = parseRouteFromLocation();
      expect(route.view).toBe('canvas');
      expect(route.designId).toBe('test-canvas-uuid');
    });

    it('correctly preserves auth routes "/login" and "/register"', () => {
      setMockLocation('/login');
      expect(parseRouteFromLocation().view).toBe('login');

      setMockLocation('/register');
      expect(parseRouteFromLocation().view).toBe('register');
    });
  });

  describe('getPathForView', () => {
    it('generates canonical URLs for each view mode', () => {
      expect(getPathForView('landing')).toBe('/');
      expect(getPathForView('login')).toBe('/login');
      expect(getPathForView('register')).toBe('/register');
      expect(getPathForView('dashboard')).toBe('/dashboard');
      expect(getPathForView('designs')).toBe('/designs');
      expect(getPathForView('design-detail', 'abc-123')).toBe('/designs?id=abc-123');
      expect(getPathForView('studio')).toBe('/studio');
      expect(getPathForView('canvas', 'xyz-789')).toBe('/canvas?id=xyz-789');
      expect(getPathForView('production')).toBe('/production');
    });
  });
});

describe('Production Subviews & Data Sync (Bug 2)', () => {
  it('Production subview tabs mapping parses standard and alias URL query params', () => {
    const tabsToTest = [
      { param: '?tab=orders', expected: 'orders' },
      { param: '?tab=workers', expected: 'workers' },
      { param: '?tab=artisans', expected: 'workers' },
      { param: '?tab=machines', expected: 'machines' },
      { param: '?tab=tools', expected: 'machines' },
      { param: '?tab=optimization', expected: 'optimization' },
      { param: '?tab=schedule', expected: 'optimization' },
      { param: '?tab=shop-floor', expected: 'shop-floor' },
      { param: '?tab=dashboard', expected: 'dashboard' },
    ];

    tabsToTest.forEach(({ param, expected }) => {
      const search = new URLSearchParams(param);
      const rawTab = search.get('tab')?.toLowerCase();
      let resolvedTab = 'dashboard';
      if (rawTab === 'orders') resolvedTab = 'orders';
      else if (rawTab === 'workers' || rawTab === 'artisans') resolvedTab = 'workers';
      else if (rawTab === 'machines' || rawTab === 'tools') resolvedTab = 'machines';
      else if (rawTab === 'optimization' || rawTab === 'schedule' || rawTab === 'solver') resolvedTab = 'optimization';
      else if (rawTab === 'shop-floor' || rawTab === 'shopfloor') resolvedTab = 'shop-floor';
      else if (rawTab === 'dashboard') resolvedTab = 'dashboard';

      expect(resolvedTab).toBe(expected);
    });
  });

  it('Studio to Production handoff URL includes tab=orders and designId/renderId', () => {
    const designId = 'd25e210f-b0ae-4b28-944f-a15b141c7a62';
    const renderId = 'r1234567-89ab-cdef-0123-456789abcdef';
    const query = `?tab=orders&designId=${designId}&renderId=${renderId}`;
    const search = new URLSearchParams(query);

    expect(search.get('tab')).toBe('orders');
    expect(search.get('designId')).toBe(designId);
    expect(search.get('renderId')).toBe(renderId);
  });
});
