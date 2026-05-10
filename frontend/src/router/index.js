import {createRouter, createWebHashHistory} from 'vue-router' // 使用 Hash 模式
import Login from "@/views/LoginRegister.vue";
import Register from "@/views/LoginRegister.vue";
import ChatHome from "@/views/ChatHome.vue";
import PipelineDemo from "@/views/PipelineDemo.vue";

const routes = [
    {
        path: '/',
        name: 'chat',
        component: ChatHome,
        meta: {
            requireAuth: false,  // 不需要强制登录
        },
    },
    {
        path: '/pipeline',
        name: 'pipeline',
        component: PipelineDemo,
    },
    {
        path: '/login',
        name: 'login',
        component: Login,
    },
    {
        path: '/register',
        name: 'register',
        component: Register,
    },
];

const router = createRouter({
    history: createWebHashHistory(),
    routes,
});

export default router;
