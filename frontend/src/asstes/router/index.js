// Vue 路由配置
import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/Home.vue';
import FaceRecognition from '@/views/FaceRecognition.vue';
import PavementDetection from '@/views/PavementDetection.vue';
import TrafficAnalysis from '@/views/TrafficAnalysis.vue';
import AlertsLogs from '@/views/AlertsLogs.vue'; // 引入日志告警页面

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home
    },
    {
        path: '/face-recognition',
        name: 'FaceRecognition',
        component: FaceRecognition
    },
    {
        path: '/pavement-detection',
        name: 'PavementDetection',
        component: PavementDetection
    },
    {
        path: '/traffic-analysis',
        name: 'TrafficAnalysis',
        component: TrafficAnalysis
    },
    {
        path: '/alerts-logs', // 新增路由
        name: 'AlertsLogs',
        component: AlertsLogs
    }
    // ... 其他路由
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

export default router;