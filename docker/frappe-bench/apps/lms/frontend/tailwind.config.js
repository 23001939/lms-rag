import frappeUIPreset from 'frappe-ui/tailwind'

export default {
	presets: [frappeUIPreset],
	content: [
		'./index.html',
		'./src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
	],
	theme: {
		extend: {
			colors: {
				core: {
					darkgreen: {
						DEFAULT: '#074942',
						50: '#E6F0EF',
						100: '#CCE2E0',
						500: '#074942',
						600: '#053732',
						700: '#042D29',
						800: '#021F1C',
						900: '#011210',
					},
					gold: {
						DEFAULT: '#F2B814',
						50: '#FEF9E7',
						100: '#FDF3CF',
						500: '#F2B814',
						600: '#D9A30E',
						700: '#B3840A',
					}
				},
				bidv: {
					emerald: {
						DEFAULT: '#006B68',
						50: '#F4F8F8',
						100: '#E0F2F1',
						200: '#B2DFDB',
						500: '#006B68',
						600: '#005754',
						700: '#00423F',
						800: '#002D2B',
						900: '#0B2827',
					},
					gold: {
						DEFAULT: '#EBAA00',
						50: '#FFFDF0',
						100: '#FFF8E1',
						200: '#FFE082',
						500: '#EBAA00',
						600: '#D49B00',
						700: '#B38000',
					}
				}
			},
			strokeWidth: {
				1.5: '1.5',
			},
			screens: {
				'2xl': '1600px',
				'3xl': '1920px',
			},
		},
	},
	plugins: [],
}
