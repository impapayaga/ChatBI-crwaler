# 项目架构
frontend/src/components: 存放 Vue 组件，自动导入并注册为全局组件。
frontend/src/layouts: 存放布局组件，用于提供页面的一致外观和感觉。
frontend/src/pages: 存放页面组件，自动转换为可导航的路由。
frontend/src/plugins: 存放插件注册代码，如 Vuetify、Pinia 和 Vue Router。
frontend/src/router: 配置 Vue Router，自动生成路由。
frontend/src/main.ts: 应用入口文件，初始化并挂载 Vue 应用。
frontend/src/assets: 存放静态资源，如图片和样式文件。

























# Vuetify (默认)

这是Vuetify的官方脚手架工具，旨在帮助您快速开始构建新的Vuetify应用程序。它设置了一个基础模板，包含所有必要的配置和标准目录结构，使您无需从头开始设置项目即可开始开发。

## ❗️ 重要链接

- 📄 [文档](https://vuetifyjs.com/)
- 🚨 [问题](https://issues.vuetifyjs.com/)
- 🏬 [商店](https://store.vuetifyjs.com/)
- 🎮 [游乐场](https://play.vuetifyjs.com/)
- 💬 [Discord](https://community.vuetifyjs.com)

## 💿 安装

使用您喜欢的包管理器设置项目。使用相应的命令安装依赖项：

| 包管理器                                                    | 命令            |
|-------------------------------------------------------------|-----------------|
| [yarn](https://yarnpkg.com/getting-started)                 | `yarn install`  |
| [npm](https://docs.npmjs.com/cli/v7/commands/npm-install)   | `npm install`   |
| [pnpm](https://pnpm.io/installation)                        | `pnpm install`  |
| [bun](https://bun.sh/#getting-started)                      | `bun install`   |

完成安装后，您的环境已准备好进行Vuetify开发。

## ✨ 特性

- 🖼️ **优化的前端栈**：利用最新的Vue 3和Vuetify 3，享受现代化、响应式的UI开发体验。 [Vue 3](https://v3.vuejs.org/) | [Vuetify 3](https://vuetifyjs.com/en/)
- 🗃️ **状态管理**：集成了[Pinia](https://pinia.vuejs.org/)，这是Vue的直观、模块化状态管理解决方案。
- 🚦 **路由和布局**：使用Vue Router进行SPA导航，并使用vite-plugin-vue-layouts组织Vue文件布局。 [Vue Router](https://router.vuejs.org/) | [vite-plugin-vue-layouts](https://github.com/JohnCampionJr/vite-plugin-vue-layouts)
- 💻 **增强的开发体验**：受益于TypeScript的静态类型检查和ESLint插件套件，确保代码质量和一致性。 [TypeScript](https://www.typescriptlang.org/) | [ESLint Plugin Vue](https://eslint.vuejs.org/)
- ⚡ **下一代工具**：由Vite驱动，体验快速的冷启动和即时HMR（热模块替换）。 [Vite](https://vitejs.dev/)
- 🧩 **自动化组件导入**：使用unplugin-vue-components简化工作流程，自动导入使用的组件。 [unplugin-vue-components](https://github.com/antfu/unplugin-vue-components)
- 🛠️ **强类型Vue**：使用vue-tsc进行Vue组件的类型检查，享受强大的开发体验。 [vue-tsc](https://github.com/johnsoncodehk/volar/tree/master/packages/vue-tsc)

这些特性旨在提供从设置到部署的无缝开发体验，确保您的Vuetify应用程序既强大又易于维护。

## 💡 使用

本节介绍如何启动开发服务器和构建生产环境项目。

### 启动开发服务器

要启动带有热重载的开发服务器，请运行以下命令。服务器将可通过[http://localhost:3000](http://localhost:3000)访问：

```bash
yarn dev
```

（使用相应的命令重复npm、pnpm和bun的操作。）

> 添加NODE_OPTIONS='--no-warnings'以抑制Vuetify导入映射过程中发生的JSON导入警告。如果您使用的是Node [v21.3.0](https://nodejs.org/en/blog/release/v21.3.0)或更高版本，可以将其更改为NODE_OPTIONS='--disable-warning=5401'。如果您不介意警告，可以从package.json的开发脚本中删除此项。

### 构建生产环境

要构建生产环境项目，请使用：

```bash
yarn build
```

（使用相应的命令重复npm、pnpm和bun的操作。）

构建过程完成后，您的应用程序将准备好在生产环境中部署。

## 💪 支持Vuetify开发

该项目是使用[Vuetify](https://vuetifyjs.com/en/)构建的，这是一个包含全面Vue组件集合的UI库。Vuetify是一个MIT许可的开源项目，得益于我们[赞助商和支持者](https://vuetifyjs.com/introduction/sponsors-and-backers/)的慷慨贡献。如果您有兴趣支持该项目，请考虑：

- [请求企业支持](https://support.vuetifyjs.com/)
- [在Github上赞助John](https://github.com/users/johnleider/sponsorship)
- [在Github上赞助Kael](https://github.com/users/kaelwd/sponsorship)
- [在Open Collective上支持团队](https://opencollective.com/vuetify)
- [在Patreon上成为赞助商](https://www.patreon.com/vuetify)
- [在Tidelift上成为订阅者](https://tidelift.com/subscription/npm/vuetify)
- [通过Paypal进行一次性捐赠](https://paypal.me/vuetify)

## 📑 许可证
[MIT](http://opensource.org/licenses/MIT)

版权所有 (c) 2016至今 Vuetify, LLC