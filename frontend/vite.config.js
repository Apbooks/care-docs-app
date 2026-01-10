import { sveltekit } from '@sveltejs/kit/vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		sveltekit(),
		SvelteKitPWA({
			srcDir: 'src',
			mode: 'production',
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
				icons: [
					{
						src: '/icon-192.png',
						sizes: '192x192',
						type: 'image/png'
					},
					{
						src: '/icon-512.png',
						sizes: '512x512',
						type: 'image/png'
					},
					{
						src: '/icon-512.png',
						sizes: '512x512',
						type: 'image/png',
						purpose: 'any maskable'
					}
				]
			},
			injectManifest: {
				globPatterns: ['**/*.{js,css,html,png,jpg,jpeg,svg,woff,woff2}']
			},
			workbox: {
				globPatterns: ['**/*.{js,css,html,png,jpg,jpeg,svg,woff,woff2}'],
				runtimeCaching: [
					{
						urlPattern: /^https:\/\/.*\/api\/.*/,
						handler: 'NetworkFirst',
						options: {
							cacheName: 'api-cache',
							networkTimeoutSeconds: 10,
							expiration: {
								maxEntries: 50,
								maxAgeSeconds: 60 * 60 * 24 // 24 hours
							},
							cacheableResponse: {
								statuses: [0, 200]
							}
						}
					},
					{
						urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
						handler: 'CacheFirst',
						options: {
							cacheName: 'image-cache',
							expiration: {
								maxEntries: 100,
								maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
							}
						}
					}
				]
			},
			devOptions: {
				enabled: true,
				type: 'module'
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
