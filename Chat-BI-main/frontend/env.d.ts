/// <reference types="vite/client" />
/// <reference types="unplugin-vue-router/client" />
/// <reference types="vite-plugin-vue-layouts/client" />

interface ImportMetaEnv {
    readonly VITE_API_BASE_URL: string
    readonly VITE_CRAWLER_API_BASE_URL: string
    // 你可以在这里添加更多的环境变量
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}