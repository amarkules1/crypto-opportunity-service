import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import CoinTable from './components/CoinTable.vue'
import PerformanceTracker from './components/PerformanceTracker.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/cointable', component: CoinTable },
    { path: '/performancetracker', component: PerformanceTracker },
    { path: '/', redirect: '/cointable' } // redirect to CoinTable as the default
  ]
})

createApp(App).use(router).mount('#app')