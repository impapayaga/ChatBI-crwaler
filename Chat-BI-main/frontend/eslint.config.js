/**
 * .eslint.js
 *
 * ESLint configuration file.
 */

import pluginVue from 'eslint-plugin-vue'
import vueTsEslintConfig from '@vue/eslint-config-typescript'
import prettierConfig from 'eslint-config-prettier'
import prettierPlugin from 'eslint-plugin-prettier'

export default [
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue}'],
  },

  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/dist-ssr/**', '**/coverage/**'],
  },

  ...pluginVue.configs['flat/recommended'],
  ...vueTsEslintConfig(),
  ...prettierConfig,

  {
    plugins: {
      prettier: prettierPlugin,
    },
    rules: {
      '@typescript-eslint/no-unused-expressions': [
        'error',
        {
          allowShortCircuit: true,
          allowTernary: true,
        },
      ],
      'vue/multi-word-component-names': 'off',
      'prettier/prettier': 'error',
    }
  },

  {
    name: 'auto-import-globals',
    globals: {
      Component: 'readonly',
      ComponentPublicInstance: 'readonly',
      ComputedRef: 'readonly',
      DirectiveBinding: 'readonly',
      EffectScope: 'readonly',
      ExtractDefaultPropTypes: 'readonly',
      ExtractPropTypes: 'readonly',
      ExtractPublicPropTypes: 'readonly',
      InjectionKey: 'readonly',
      MaybeRef: 'readonly',
      MaybeRefOrGetter: 'readonly',
      PropType: 'readonly',
      Ref: 'readonly',
      VNode: 'readonly',
      WritableComputedRef: 'readonly',
      computed: 'readonly',
      createApp: 'readonly',
      customRef: 'readonly',
      defineAsyncComponent: 'readonly',
      defineComponent: 'readonly',
      effectScope: 'readonly',
      getCurrentInstance: 'readonly',
      getCurrentScope: 'readonly',
      h: 'readonly',
      inject: 'readonly',
      isProxy: 'readonly',
      isReactive: 'readonly',
      isReadonly: 'readonly',
      isRef: 'readonly',
      markRaw: 'readonly',
      nextTick: 'readonly',
      onActivated: 'readonly',
      onBeforeMount: 'readonly',
      onBeforeUnmount: 'readonly',
      onBeforeUpdate: 'readonly',
      onDeactivated: 'readonly',
      onErrorCaptured: 'readonly',
      onMounted: 'readonly',
      onRenderTracked: 'readonly',
      onRenderTriggered: 'readonly',
      onScopeDispose: 'readonly',
      onServerPrefetch: 'readonly',
      onUnmounted: 'readonly',
      onUpdated: 'readonly',
      onWatcherCleanup: 'readonly',
      provide: 'readonly',
      reactive: 'readonly',
      readonly: 'readonly',
      ref: 'readonly',
      resolveComponent: 'readonly',
      shallowReactive: 'readonly',
      shallowReadonly: 'readonly',
      shallowRef: 'readonly',
      toRaw: 'readonly',
      toRef: 'readonly',
      toRefs: 'readonly',
      toValue: 'readonly',
      triggerRef: 'readonly',
      unref: 'readonly',
      useAttrs: 'readonly',
      useCssModule: 'readonly',
      useCssVars: 'readonly',
      useId: 'readonly',
      useModel: 'readonly',
      useRoute: 'readonly',
      useRouter: 'readonly',
      useSlots: 'readonly',
      useTemplateRef: 'readonly',
      watch: 'readonly',
      watchEffect: 'readonly',
      watchPostEffect: 'readonly',
      watchSyncEffect: 'readonly'
    }
  }
]