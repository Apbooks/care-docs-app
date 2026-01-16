import { sveltekit } from '@sveltejs/kit/vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		sveltekit(),
		SvelteKitPWA({
			srcDir: 'src',
			strategies: 'injectManifest',
			filename: 'service-worker.js',
			scope: '/',
			base: '/',
			manifest: {
				short_name: 'CareDocsApp',
				name: 'Care Documentation App',
				description: 'Track medications, feeding, and care activities',
				theme_color: '#3b82f6',
				background_color: '#ffffff',
				display: 'standalone',
				orientation: 'portrait',
				start_url: '/',
				icons: [
					{
						src: '/icon.svg',
						sizes: 'any',
						type: 'image/svg+xml'
					},
					{
						src: '/icon.svg',
						sizes: '192x192',
						type: 'image/svg+xml',
						purpose: 'any'
					},
					{
						src: '/icon.svg',
						sizes: '512x512',
						type: 'image/svg+xml',
						purpose: 'any maskable'
					}
				]
			},
			injectManifest: {
				globPatterns: ['**/*.{js,css,html,png,jpg,jpeg,svg,woff,woff2,ico}'],
				globIgnores: ['**/node_modules/**/*', 'sw.js', 'workbox-*.js']
			},
			devOptions: {
				enabled: true,
				type: 'module',
				navigateFallback: '/'
			}
		})
	],
	server: {
		port: 3000,
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
