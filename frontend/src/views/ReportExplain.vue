<script setup>
import {ref} from "vue";
import MarkdownIt from "markdown-it";
import {ElMessage} from "element-plus";

const md = new MarkdownIt();

const reportText = ref("");
const question = ref("");
const selectedFile = ref(null);

const output = ref("");
const loading = ref(false);

const onFileChange = (file) => {
  // element-plus el-upload on-change 传入 UploadFile
  selectedFile.value = file?.raw ?? null;
};

const rendered = () => md.render(output.value || "");

const streamNdjson = async (response) => {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let done = false;
  while (!done) {
    const {value, done: readerDone} = await reader.read();
    done = readerDone;
    if (!value) continue;
    const chunk = decoder.decode(value, {stream: true});
    const lines = chunk.split("\n");
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const parsed = JSON.parse(line);
        if (parsed?.token && parsed?.is_complete === false) {
          output.value += parsed.token;
        }
      } catch (e) {
        // ignore broken line
      }
    }
  }
};

const explain = async () => {
  output.value = "";
  loading.value = true;
  try {
    const token = localStorage.getItem("token");

    if (selectedFile.value) {
      const fd = new FormData();
      fd.append("file_data", selectedFile.value);
      fd.append("question", question.value || "");
      const resp = await fetch("/api/extra/report/image", {
        method: "POST",
        headers: {Authorization: `Bearer ${token}`},
        body: fd,
      });
      await streamNdjson(resp);
    } else {
      if (!reportText.value.trim()) {
        ElMessage({type: "warning", message: "请先粘贴报告文本或上传报告图片"});
        return;
      }
      const resp = await fetch("/api/extra/report/text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({text: reportText.value}),
      });
      await streamNdjson(resp);
    }
  } catch (e) {
    ElMessage({type: "error", message: `解读失败：${e.message || e}`});
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="page">
    <div class="panel">
      <div class="header">
        <div class="title">报告解读</div>
        <div class="subtitle">支持粘贴报告文字或上传报告图片（OCR + DeepSeek 流式解读）。</div>
      </div>

      <div class="grid">
        <div class="card">
          <div class="card-title">输入</div>
          <el-upload
              :show-file-list="false"
              :on-change="onFileChange"
              accept=".jpg,.jpeg,.png,.bmp,.webp"
          >
            <el-button type="primary" plain>上传报告图片（可选）</el-button>
          </el-upload>
          <div class="hint" v-if="selectedFile">已选择：{{ selectedFile.name }}</div>

          <el-input
              v-model="question"
              placeholder="可选：你想重点问什么？比如“异常指标严重吗？”"
              size="large"
              class="mt"
          />

          <el-input
              v-model="reportText"
              type="textarea"
              :rows="10"
              placeholder="没有图片时请粘贴报告原文..."
              class="mt"
          />

          <div class="actions">
            <el-button type="success" size="large" :loading="loading" @click="explain">
              开始解读（流式）
            </el-button>
            <el-button size="large" @click="() => { output=''; reportText=''; question=''; selectedFile=null }">
              清空
            </el-button>
          </div>
        </div>

        <div class="card">
          <div class="card-title">输出</div>
          <div class="output markdown-body" v-html="rendered()"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 96px 24px 32px;
  display: flex;
  justify-content: center;
  background:
      radial-gradient(circle at top left, #e0f2fe 0, transparent 45%),
      radial-gradient(circle at bottom right, #ede9fe 0, transparent 50%),
      #f5f7fb;
}

.panel {
  width: 100%;
  max-width: 1200px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 28px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
  padding: 24px 28px;
}

.header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 18px;
}

.title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #0f172a;
}

.subtitle {
  color: #6b7280;
  font-size: 0.9rem;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.card {
  background: #f9fafb;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 18px;
  padding: 16px;
}

.card-title {
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 12px;
}

.hint {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #6b7280;
}

.mt {
  margin-top: 12px;
}

.actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.output {
  min-height: 420px;
  max-height: 70vh;
  overflow: auto;
  background: white;
  border-radius: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

@media (max-width: 960px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>


