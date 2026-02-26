<script setup>
import { ref, onMounted } from 'vue';

const isLoaded = ref(false);

onMounted(() => {
  setTimeout(() => {
    isLoaded.value = true;
  }, 100);
});
</script>

<template>
  <div class="back-ground">
    <section class="main-section">
      <div class="hero-grid" :class="{ 'loaded': isLoaded }">
        <div class="hero-content">
          <div class="hero-badge">
            <span class="badge-icon">🔬</span>
            <span>AI-Powered TCM Diagnosis</span>
          </div>

          <h1 class="gradient-title">
            <span class="title-line">Intelligent</span>
            <span class="title-line highlight">Tongue Diagnosis</span>
            <span class="title-line">for Everyone</span>
          </h1>

          <p class="subtitle">
            Capture your tongue, let AI read subtle TCM tongue features, and receive easy-to-understand health
            suggestions in seconds.
          </p>

          <div class="feature-tags">
            <span class="tag">✨ Deep learning tongue analysis</span>
            <span class="tag">📷 One-tap photo upload</span>
            <span class="tag">📜 TCM-style interpretation</span>
          </div>

          <div class="cta-section">
            <router-link to="/check" class="cta-button primary">
              <span class="button-text">Start Tongue Diagnosis</span>
              <div class="button-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M5 12H19M19 12L13 6M19 12L13 18" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </router-link>
          </div>
        </div>

        <div class="hero-visual">
          <div class="tongue-card">
            <img src="@/assets/Chat_Tongue.jpg" alt="AI Tongue Preview" class="tongue-image">
            <div class="tongue-overlay">
              <div class="overlay-chip">舌色 · Tongue Color</div>
              <div class="overlay-chip">苔色 · Coating</div>
              <div class="overlay-chip">厚薄 · Thickness</div>
              <div class="overlay-chip">腻腐 · Greasy/Furred</div>
            </div>
          </div>
          <div class="hero-metrics">
            <div class="metric-card">
              <div class="metric-label">Avg. analysis time</div>
              <div class="metric-value">&lt; 40 s</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">Tongue feature coverage</div>
              <div class="metric-value">4+ key signs</div>
            </div>
          </div>
        </div>
      </div>

      <div class="steps-row">
        <div class="step-card">
          <div class="step-index">01</div>
          <div class="step-title">Capture your tongue</div>
          <div class="step-body">
            Use natural light, relax your tongue and keep it flat to get a clear, reliable tongue photo.
          </div>
        </div>
        <div class="step-card">
          <div class="step-index">02</div>
          <div class="step-title">AI analyses TCM features</div>
          <div class="step-body">
            Our model detects tongue color, coating, thickness and greasy signs based on TCM diagnostic principles.
          </div>
        </div>
        <div class="step-card">
          <div class="step-index">03</div>
          <div class="step-title">Receive your insights</div>
          <div class="step-body">
            Get concise explanations and health suggestions in a chat-like interface, ready to discuss with a doctor.
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.back-ground {
  min-height: 100vh;
  padding: 96px 24px 32px;
  display: flex;
  align-items: stretch;
  justify-content: center;
  background:
      radial-gradient(circle at top left, #e0f2fe 0, transparent 45%),
      radial-gradient(circle at bottom right, #ede9fe 0, transparent 50%),
      #f5f7fb;
}

.header {
  position: relative;
  z-index: 10;
}

.main-section {
  position: relative;
  z-index: 2;
  padding: 32px 40px 28px;
  min-height: 0;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 28px;
  box-shadow:
    0 18px 45px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(148, 163, 184, 0.08);
}

.container {
  max-width: 100%;
  padding: 0;
  margin: 0;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 40px;
  align-items: center;
  margin-bottom: 32px;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-grid.loaded {
  opacity: 1;
  transform: translateY(0);
}

.hero-content {
  padding-right: 8px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(37, 99, 235, 0.06);
  border-radius: 999px;
  color: #1d4ed8;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 20px;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.badge-icon {
  font-size: 0.9rem;
}

.gradient-title {
  font-size: 2.9rem;
  line-height: 1.1;
  margin-bottom: 20px;
  font-weight: 800;
  color: #0f172a;
}

.title-line {
  display: block;
}

.title-line.highlight {
  background: linear-gradient(45deg, #2563eb 0%, #14b8a6 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  position: relative;
}

.subtitle {
  color: #4b5563;
  font-size: 1.25rem;
  line-height: 1.7;
  margin-bottom: 28px;
  max-width: 580px;
  font-weight: 400;
}

.feature-tags {
  display: flex;
  gap: 12px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.tag {
  padding: 8px 16px;
  background: #eff6ff;
  border-radius: 25px;
  color: #1d4ed8;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.cta-section {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 26px;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 500;
  font-size: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: none;
  cursor: pointer;
}

.cta-button.primary {
  background: linear-gradient(45deg, #2563eb 0%, #22c55e 100%);
  color: white;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.35);
}

.cta-button.secondary {
  background: #ffffff;
  color: #111827;
  border: 1px solid rgba(148, 163, 184, 0.5);
}

.cta-button:hover {
  transform: translateY(-3px);
}

.cta-button.primary:hover {
  box-shadow: 0 18px 40px rgba(37, 99, 235, 0.45);
}

.cta-button.secondary:hover {
  background: #f9fafb;
}

.button-icon {
  transition: transform 0.3s ease;
}

.cta-button:hover .button-icon {
  transform: translateX(4px);
}

.card-group {
  display: grid;
  gap: 24px;
  align-self: stretch;
}

.featured-card {
  background: #ffffff;
  border-radius: 22px;
  padding: 28px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative;
  overflow: hidden;
}

.featured-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 22px 55px rgba(15, 23, 42, 0.18);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.card-icon.featured {
  width: 60px;
  height: 60px;
  background: radial-gradient(circle at 30% 0, #bfdbfe, #2563eb);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.card-badge {
  padding: 4px 12px;
  background: #ecfdf3;
  color: #15803d;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.featured-card h3 {
  color: #0f172a;
  font-size: 1.6rem;
  margin-bottom: 16px;
  font-weight: 700;
}

.featured-card p {
  color: #4b5563;
  line-height: 1.65;
  font-size: 0.98rem;
  margin-bottom: 24px;
}

.card-stats {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.feature-card {
  background: #f9fafb;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 20px;
  transition: all 0.3s ease;
  overflow: hidden;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.14);
}

.card-content {
  padding: 28px;
}

.card-icon {
  width: 50px;
  height: 50px;
  background: radial-gradient(circle at 30% 0, #e0f2fe, #bfdbfe);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  color: #667eea;
}

.feature-card h3 {
  color: #111827;
  font-size: 1.5rem;
  margin-bottom: 12px;
  font-weight: 600;
}

.feature-card p {
  color: #4b5563;
  line-height: 1.6;
  font-size: 0.95rem;
  margin-bottom: 20px;
}

.card-features {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.feature-item {
  padding: 6px 12px;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.hero-visual {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tongue-card {
  position: relative;
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
  background: radial-gradient(circle at 0 0, rgba(59, 130, 246, 0.18), transparent 55%),
  #020617;
}

.tongue-image {
  width: 100%;
  display: block;
  object-fit: cover;
  opacity: 0.96;
}

.tongue-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-wrap: wrap;
  align-content: flex-end;
  gap: 8px;
  padding: 14px 16px;
  background: linear-gradient(to top, rgba(15, 23, 42, 0.85), transparent 55%);
}

.overlay-chip {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  color: #e5e7eb;
  border: 1px solid rgba(148, 163, 184, 0.7);
  background: rgba(15, 23, 42, 0.6);
}

.hero-metrics {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.metric-card {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 14px;
  background: #eff6ff;
  border: 1px solid rgba(191, 219, 254, 0.9);
}

.metric-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1d4ed8;
}

.steps-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.step-card {
  padding: 16px 18px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
}

.step-index {
  font-size: 0.8rem;
  font-weight: 600;
  color: #9ca3af;
  margin-bottom: 6px;
}

.step-title {
  font-size: 0.98rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 6px;
}

.step-body {
  font-size: 0.86rem;
  line-height: 1.5;
  color: #6b7280;
}

@media (max-width: 1024px) {
  .back-ground {
    padding: 88px 16px 24px;
  }

  .main-section {
    padding: 28px 24px;
  }

  .hero-grid {
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
    gap: 28px;
  }

  .gradient-title {
    font-size: 2.4rem;
  }

  .hero-content {
    padding-right: 0;
    margin-bottom: 60px;
  }

  .container {
    padding: 0 20px;
  }
}

@media (max-width: 768px) {
  .main-section {
    padding: 24px 18px;
    border-radius: 22px;
  }

  .gradient-title {
    font-size: 2.1rem;
  }

  .main-section {
    padding: 24px 16px 28px;
  }

  .cta-section {
    flex-direction: column;
    align-items: stretch;
  }

  .cta-button {
    justify-content: center;
  }

  .feature-tags {
    justify-content: center;
  }

  .card-stats {
    justify-content: space-around;
  }

  .hero-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .hero-visual {
    order: -1;
  }

  .steps-row {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 480px) {
  .back-ground {
    padding: 80px 12px 20px;
  }

  .main-section {
    padding: 20px 14px;
    border-radius: 18px;
  }

  .gradient-title {
    font-size: 1.8rem;
  }

  .subtitle {
    font-size: 1.125rem;
  }

  .container {
    padding: 0 16px;
  }

  .featured-card,
  .card-content {
    padding: 24px;
  }
}
</style>
