/**
 * 导航菜单配置
 * PC端侧边栏和移动端顶部导航栏共享此配置
 */

export interface NavigationItem {
  title: string
  icon: string
  to?: string
  disabled?: boolean
  tooltip?: string
}

export const navigationMenus: NavigationItem[] = [
  {
    title: '对话',
    icon: 'mdi-message-text',
    to: '/',
    tooltip: '对话'
  },
  // 数据爬取管理功能（生产环境已禁用，保留代码以便后续启用）
  // {
  //   title: '数据爬取管理',
  //   icon: 'mdi-spider-web',
  //   to: '/scraper-management',
  //   tooltip: '数据爬取管理',
  //   disabled: true
  // },
  {
    title: 'AI模型配置',
    icon: 'mdi-tune-variant',
    to: '/ai-model-config',
    tooltip: 'AI模型配置'
  },
  {
    title: '数据集管理',
    icon: 'mdi-database-cog',
    to: '/dataset-management',
    tooltip: '数据集管理'
  },
  {
    title: 'MinIO文件管理',
    icon: 'mdi-cloud-upload',
    to: '/minio-manager',
    tooltip: 'MinIO文件管理'
  }
]
