<script lang="ts" setup>
import {nextTick, onMounted, ref, watch} from 'vue';
import Main from "@/components/mainPage/mainContainer.vue";
import GuidePage from "@/components/mainPage/guidePage.vue";
import axios from "axios";

const showGuide = ref(true);
const guidePageRef = ref(null);
const activeItem = ref<string | null | number>(null);
const mainPageRef = ref(null);
const items = ref([]);
const newItemLabel = ref('');
let itemIdCounter = 10000000;

const handleItemClick = async (id: string | number) => {
  showGuide.value = false;
  await nextTick();
  console.log(`选中项: ${id}`);
  const tempTip = items.value.find(item => item.id === id).temp
  if (tempTip) {
    console.log("临时页面")
    mainPageRef.value.resetPage();
    activeItem.value = id;
    mainPageRef.value.setTempName(items.value.find(item => item.id === activeItem.value).label)
    return
  }
  axios.get("/model/record/" + id, {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('token')
    }, timeout: 20000
  }).then(res => {

    console.log("选中页面的数据", res.data.data.records)
    const data = res.data.data.records
    mainPageRef.value.inputData(data.map(item => {
          return {
            text: item.content,
            isUser: item.role == 1,
            loading: false,
            isPicture: false,
            time: new Date(item.create_at).toLocaleString('default', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            }),
          }
        }), id
    )
    activeItem.value = id;
  }).catch(error => {
    console.log(error);
  })

};

watch(activeItem, (newVal) => {

});

const addItem = () => {
  if (!newItemLabel.value.trim()) {
    return;
  }
  const newItemId = ++itemIdCounter;
  items.value.push({
    id: newItemId,
    label: newItemLabel.value.trim(),
    temp: true
  });
  handleItemClick(newItemId);
  newItemLabel.value = '';
};

const removeItem = (targetId: string) => {
  items.value = items.value.filter(item => item.id !== targetId);
  if (activeItem.value === targetId) {
    activeItem.value = items.value.length ? items.value[0].id : null;
  }
};

const formatData = (data: any) => {
  return data.map(item => {
    return {
      id: item.session_id,
      label: item.name,
      temp: false
    }
  })
}

onMounted(() => {
  axios.get("/model/session", {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('token')
    }, timeout: 40000
  }).then(res => {
    console.log("初始化数据", res.data.data)
    items.value = formatData(res.data.data)
    if (items.value.length) {
      guidePageRef.value.changeGuideText("View Details of the Record")
    } else guidePageRef.value.changeGuideText(" Add")
  }).catch(error => {
    console.log(error);
  })
})
;

const handleBackId = (id: string) => {
  items.value[items.value.length - 1].id = id
  activeItem.value = id
  items.value[items.value.length - 1].temp = false
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    addItem();
  }
};
</script>

<template>
  <div class="back-ground">
    <div class="ai-shell">
      <div class="ai-shell-header">
        <div class="ai-title-block">
          <div class="ai-title">AI Tongue Diagnosis Lab</div>
          <div class="ai-subtitle">
            Upload your tongue image and chat with the AI for Traditional Chinese Medicine based insights.
          </div>
        </div>
        <div class="ai-meta">
          <span class="ai-meta-pill">⚙ Real‑time analysis</span>
          <span class="ai-meta-pill">🩺 TCM tongue features</span>
        </div>
      </div>

      <div class="content">
        <div class="sidebar-container">
          <div class="sidebar-header">
            <div class="sidebar-header-text">
              <div class="sidebar-title">Diagnosis Sessions</div>
              <div class="sidebar-subtitle">Manage and review your tongue analysis history.</div>
            </div>
            <el-button type="primary" size="small" @click="addItem" @keydown="handleKeyDown">
              New
            </el-button>
          </div>
          <el-input
              v-model="newItemLabel"
              placeholder="Name this session (e.g. 'Morning check')"
              size="small"
              class="sidebar-input"
          />
          <div class="sidebar-list">
            <div
                v-for="item in items"
                :key="item.id"
                :class="['sidebar-item', { active: activeItem === item.id }]"
                @click="handleItemClick(item.id)"
            >
              <div class="sidebar-item-main">
                <span class="sidebar-item-label">{{ item.label }}</span>
                <span v-if="item.temp" class="sidebar-item-badge">Draft</span>
              </div>
            </div>
          </div>
        </div>
        <div class="main-container">
          <GuidePage v-if="showGuide" ref="guidePageRef"/>
          <Main ref="mainPageRef" @back-id="handleBackId" v-else/>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.back-ground {
  min-height: 100vh;
  padding: 96px 24px 32px;
  display: flex;
  justify-content: center;
  align-items: stretch;
  background:
      radial-gradient(circle at top left, #fee2e2 0, transparent 45%),
      radial-gradient(circle at bottom right, #e0f2fe 0, transparent 55%),
      #f5f7fb;
}

.ai-shell {
  width: 100%;
  max-width: 1280px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 28px;
  box-shadow:
      0 18px 45px rgba(15, 23, 42, 0.12),
      0 0 0 1px rgba(148, 163, 184, 0.08);
  padding: 24px 28px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.ai-shell-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.ai-title-block {
  display: flex;
  gap: 5px;
  flex-direction: column;
}

.ai-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #0f172a;
}

.ai-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
  max-width: 520px;
}

.ai-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-meta-pill {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #1e293b;
  background: #eff6ff;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.content {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 18px;
}

.main-container {
  flex: 1;
  padding: 0;
  border-radius: 20px;
  background: #f9fafb;
  border: 1px solid rgba(226, 232, 240, 0.9);
  overflow: hidden;
}

.sidebar-container {
  width: 260px;
  height: 100%;
  background: #f9fafb;
  border-radius: 18px;
  padding: 14px 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.sidebar-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.sidebar-header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #0f172a;
}

.sidebar-subtitle {
  font-size: 0.78rem;
  color: #9ca3af;
}

.sidebar-input {
  margin-top: 4px;
}

.sidebar-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 6px;
  overflow-y: auto;
}

.sidebar-item {
  background: #ffffff;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.sidebar-item:hover {
  border-color: rgba(59, 130, 246, 0.35);
  background: #f1f5f9;
}

.sidebar-item.active {
  background: linear-gradient(135deg, #2563eb 0%, #22c55e 100%);
  color: white;
  border-color: transparent;
}

.sidebar-item-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.sidebar-item-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-item-badge {
  font-size: 0.7rem;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.9);
  color: #0f172a;
}

@media (max-width: 1024px) {
  .back-ground {
    padding: 88px 16px 24px;
  }

  .ai-shell {
    padding: 20px 18px;
  }

  .content {
    gap: 14px;
  }

  .sidebar-container {
    width: 230px;
  }
}

@media (max-width: 768px) {
  .back-ground {
    padding: 80px 12px 20px;
  }

  .ai-shell {
    padding: 18px 14px;
  }

  .ai-shell-header {
    flex-direction: column;
    gap: 10px;
  }

  .content {
    flex-direction: column;
  }

  .sidebar-container {
    width: 100%;
    height: auto;
    flex-shrink: 0;
  }
}
</style>
