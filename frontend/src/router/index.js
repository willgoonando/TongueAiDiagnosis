import {createRouter, createWebHashHistory} from 'vue-router' // 使用 Hash 模式
import Home from '../views/Home.vue'
import Check from "../views/Check.vue";
import ReportExplain from "../views/ReportExplain.vue";
import DrugBox from "../views/DrugBox.vue";
import Login from "@/views/LoginRegister.vue";
import Register from "@/views/LoginRegister.vue";

const routes = [
    {
        path: '/home',
        name: 'home',
        component: Home,
        meta: {
            requireAuth: true,
        },
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
    {
        path: '/check',
        name: 'check',
        component: Check,
        meta: {
            requireAuth: true,
        },
    },
    {
        path: '/exam/coating',
        name: 'exam_coating',
        component: Check,
        meta: {
            requireAuth: true,
        },
    },
    {
        path: '/exam/report',
        name: 'exam_report',
        component: ReportExplain,
        meta: {
            requireAuth: true,
        },
    },
    {
        path: '/exam/drugbox',
        name: 'exam_drugbox',
        component: DrugBox,
        meta: {
            requireAuth: true,
        },
    },
    {
        path: '/',
        redirect: '/home',
    },

];

const router = createRouter({
    history: createWebHashHistory(),
    routes,
});

export default router;
