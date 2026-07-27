import { defineConfig, presetUno } from 'unocss'

export default defineConfig({
  presets: [presetUno()],
  shortcuts: {
    'paper': 'bg-white dark:bg-[#2e2f35] rounded-lg shadow-[0_1px_4px_rgba(0,0,0,0.05),0_4px_24px_rgba(0,0,0,0.04)]',
    'text-main': 'text-[#262626] dark:text-[#b8b9bd]',
    'text-secondary': 'text-[#8a8f8d] dark:text-[#76777d]',
    'link-brand': 'text-[#00b96b] dark:text-[#3aad86] hover:underline',
    'border-base': 'border border-[#e7e9e8] dark:border-[#383940]',
  },
  theme: {
    colors: {
      brand: '#00b96b',
      'brand-dark': '#3aad86',
      'page-bg': '#f4f5f5',
      'page-bg-dark': '#2a2b30',
      'paper-bg': '#ffffff',
      'paper-bg-dark': '#2e2f35',
    },
  },
})
