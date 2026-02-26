<template>
  <div
      class="draggable-container"
      :style="{ top: `${position.y}px`, left: `${position.x}px`, position: 'absolute', transition: 'top 0.s ease, left 0.s ease' }"
      ref="draggableContainer"
  >
    <div v-if="sendPic" class="upload-wrapper">
      <el-icon class="arrow-left">
        <ArrowRightBold/>
      </el-icon>
      <div v-if="isUploading">
        <Steps ref="stepRef"/>
      </div>
      <div v-else>
        <UploadPicture @success="startQuest" style="margin-top: 5px"/>
      </div>
      <el-icon class="arrow-right">
        <ArrowLeftBold/>
      </el-icon>
    </div>
    <div class="drag-handle" @mousedown="startDrag" v-if="!sendPic">
      <el-icon>
        <Rank/>
      </el-icon>
    </div>
    <input @keydown="handleKeyDown" class="message-input" v-model="inputValue" placeholder="Please enter here."
           style="height: auto;" v-if="!sendPic">
    <el-button type="success" :icon="Promotion" @click="sendToMain" size="large" style="font-size: 20px;" circle
               v-if="!sendPic"/>
    <el-button
        :type="isRecording ? 'warning' : 'primary'"
        :icon="isRecording ? CircleClose:Microphone"
        @click="toggleVoiceRecognition"
        size="large"
        :loading="isLoading"
        style="font-size: 20px;"
        circle
        v-if="!sendPic"
    />
  </div>
</template>

<script setup lang="ts">
import {ref, reactive, onBeforeMount, computed, nextTick} from 'vue'
import {Promotion, Rank, Microphone, CircleClose, ArrowLeftBold, ArrowRightBold} from "@element-plus/icons-vue";
import {ElMessage} from "element-plus";
import {useStateStore} from '@/stores/stateStore';
import UploadPicture from '@/components/UploadPicture.vue';
import Steps from "@/components/Steps.vue";
import axios from "axios";

const stateStore = useStateStore();
let sendPic = ref(true);
let isUploading = ref(false);
const stepRef = ref(null);
const emit = defineEmits(['send-to-main', 'send-picture']);
let inputValue = ref('');
let ask_tip = 0;
const sendToMain = () => {
  emit('send-to-main', ask_tip, inputValue.value);
  ask_tip += 1;
  inputValue.value = '';
};

const isRecording = ref(false);
const isLoading = ref(false);
const result = ref("");

let baseURL = '';
onBeforeMount(() => {
  if (stateStore.baseUrl == "0") {
    ErrorPop("Please set an url", 5000)
  }
  baseURL = stateStore.baseUrl;
});
let recognition = null;

const tongueDictionary = {
  color: [
    "舌色：淡白舌,",
    "舌色：淡红舌,",
    "舌色：红舌,",
    "舌色：绛舌,",
    "舌色：青紫舌,"
  ],
  outcolor: [
    "舌苔颜色：白苔,",
    "舌苔颜色：黄苔,",
    "舌苔颜色：灰黑苔,"
  ],
  rot: [
    "舌苔腻,",
    "舌苔腐,"
  ],
  thick: [
    "舌头薄,",
    "舌头厚,"
  ]
};

async function getRecordData() {
  try {
    const response = await axios.get('/user/record', {
      headers: {
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      }
    });
    return response.data
  } catch (error) {
    console.error('获取 /user/record 失败:', error);
    return null;
  }
}

const toggleVoiceRecognition = () => {
  if (isRecording.value) {
    stopRecognition();
  } else {
    startRecognition();
  }
};

const resetLoading = () => {
  stepRef.value.resetCountdown()
}

if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false; // 设为非连续模式
  recognition.interimResults = false; // 只返回最终结果
  recognition.lang = 'zh-CN'; // 设定语言为中文

  recognition.onstart = () => {
    isRecording.value = true;

  };

  recognition.onresult = (event) => {
    inputValue.value += event.results[0][0].transcript;
  };

  recognition.onerror = (event) => {
    ErrorPop('语音识别出错，请重试');
  };

  recognition.onend = () => {
    isRecording.value = false;
  };
} else {
  console.warn('当前浏览器不支持语音识别');
}

const startRecognition = () => {

  if (recognition) {
    recognition.start();
    console.log("开始语音识别")
  } else {
    ErrorPop('您的浏览器不支持语音识别');
  }
};

const stopRecognition = () => {
  if (recognition) {
    console.log("停止语音识别")
    recognition.stop();
  }
};

let audioType = ref("De");

interface Position {
  x: number;
  y: number;
}

interface Offset {
  x: number;
  y: number;
}

const position = reactive<Position>({x: window.innerWidth - 850, y: window.innerHeight - 250}) // 初始位置
const offset = reactive<Offset>({x: 0, y: 0})
let isDragging = ref<boolean>(false)
const draggableContainer = ref<HTMLDivElement | null>(null)

const startDrag = (event: MouseEvent): void => {
  if (draggableContainer.value) {
    const rect = draggableContainer.value.getBoundingClientRect()
    isDragging.value = true
    offset.x = event.clientX - rect.left
    offset.y = event.clientY - rect.top
    document.addEventListener('mousemove', onDrag)
    document.addEventListener('mouseup', endDrag)
  }
}

const onDrag = (event: MouseEvent): void => {
  if (isDragging.value) {
    position.x = Math.max(0, Math.min(event.clientX - offset.x, window.innerWidth - (draggableContainer.value?.offsetWidth || 0)));
    position.y = Math.max(0, Math.min(event.clientY - offset.y, window.innerHeight - (draggableContainer.value?.offsetHeight || 0)));
  }
};

const endDrag = (): void => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    sendToMain();
  }
};

const ErrorPop = (info: string, time = 3000) => {
  ElMessage({
    showClose: true,
    message: info,
    type: 'error',
    duration: time
  })
}

let pic64 = ref("")

const startQuest = async (info) => {
  if (info.success) {
    pic64.value = info.base64
  }
  console.log("开始");
  emit("send-picture", {base64: pic64.value,fileData: info.fileData})
  startLoading();
}

async function pollGetRecord(interval = 2000, startTime = Date.now()) {
  try {
    const responseData = await getRecordData();
    const data = responseData.data;

    if (data && data[data.length - 1].state === 1) {
      const endTime = Date.now(); // 记录结束时间
      const elapsedTime = (endTime - startTime) / 1000; // 计算总耗时（秒）

      console.log("✅ 获取到符合条件的数据:", data[data.length - 1].result);
      console.log(`🎯 轮询耗时: ${elapsedTime.toFixed(2)} 秒`);
      const result = data[data.length - 1].result
      let ans = ''

      ans += tongueDictionary.color[result.tongue_color]
      ans += tongueDictionary.outcolor[result.coating_color]
      ans += tongueDictionary.thick[result.tongue_thickness]
      ans += tongueDictionary.rot[result.rot_greasy]
      console.log(ans)
      emit("send-picture", {base64: pic64.value, ans: ans})
      startChat();


      return data[data.length - 1].result;
    }

    console.log("🔄 数据不符合条件，继续轮询...");
    setTimeout(() => pollGetRecord(interval, startTime), interval); // 递归调用继续轮询
  } catch (error) {
    console.error("❌ 轮询获取数据失败:", error);
    setTimeout(() => pollGetRecord(interval, startTime), interval); // 发生错误时继续轮询
  }
}

const backUploading = () => {
  sendPic.value = true
  isUploading.value = false
}

const startLoading = async () => {
  isUploading.value = true
  await nextTick()
  resetLoading();
}

const startChat = () => {
  sendPic.value = false
  isUploading.value = false
}

const getReturn = (data) => {
  if (data.success) startChat()
  else backUploading()
}
defineExpose({startChat, startLoading, backUploading, getReturn})
</script>

<style scoped>
.draggable-container {
  display: flex;
  align-items: center;
  width: 560px;
  background: radial-gradient(circle at 0 0, rgba(59, 130, 246, 0.18), transparent 60%),
  rgba(15, 23, 42, 0.95);
  border-radius: 999px;
  padding: 10px 16px;
  box-shadow:
      0 18px 40px rgba(15, 23, 42, 0.45),
      0 0 0 1px rgba(148, 163, 184, 0.5);
  cursor: move;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
  justify-content: center;
  color: #e5e7eb;
}

.draggable-container:hover {
  box-shadow:
      0 26px 55px rgba(15, 23, 42, 0.6),
      0 0 0 1px rgba(148, 163, 184, 0.7);
  transform: translateY(-2px);
}

.drag-handle {
  margin-right: 10px;
  cursor: grab;
  color: #9ca3af;
}

.message-input {
  flex: 1;
  border: none;
  padding: 10px 14px;
  outline: none;
  border-radius: 999px;
  font-size: 15px;
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  line-height: 1.5;
  background-color: rgba(15, 23, 42, 0.9);
  color: #e5e7eb;
}

.message-input::placeholder {
  color: #6b7280;
}

.upload-wrapper {
  display: flex;
  align-items: center;
  gap: 20px;
}

.arrow-left, .arrow-right {
  font-size: 24px;
  color: #93c5fd;
}

.arrow-left:hover, .arrow-right:hover {
  color: #bfdbfe;
}
</style>