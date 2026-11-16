<template>
  <div class="about">
    <div class="studio-page-header">
      <div class="header-titles">
        <h1>关于系统</h1>
        <p>SAU 自媒体自动化运营与多平台分发工作台说明</p>
      </div>
    </div>

    <el-card class="about-card" shadow="never">
      <div class="about-hero">
        <div class="hero-icon">SAU</div>
        <div>
          <h2>自媒体自动化运营系统</h2>
          <p class="version">social-auto-upload · 本地多平台内容分发引擎</p>
        </div>
      </div>

      <el-divider />

      <div class="about-section">
        <h3>系统简介</h3>
        <p>
          本系统是一款强大的自动化工具，帮助内容创作者和运营人员一键将视频内容高效发布到多个国内外主流社交媒体平台。
          支持视频上传、定时发布等功能。
        </p>
      </div>

      <div class="about-section">
        <h3>支持平台</h3>
        <div class="platform-tags">
          <span class="plat-pill douyin">抖音</span>
          <span class="plat-pill kuaishou">快手</span>
          <span class="plat-pill channels">视频号</span>
          <span class="plat-pill xhs">小红书</span>
        </div>
      </div>

      <div class="about-section">
        <h3>核心功能</h3>
        <div class="feature-grid">
          <div class="feature-item">多平台账号管理与登录状态维护</div>
          <div class="feature-item">视频素材批量上传与在线预览</div>
          <div class="feature-item">一键多平台与多任务并行发布</div>
          <div class="feature-item">定时排期与批量队列分发</div>
          <div class="feature-item">账号 Cookie 一键导出与导入</div>
        </div>
      </div>

      <div class="about-section">
        <h3>技术栈</h3>
        <div class="tech-tags">
          <el-tag effect="light">Vue 3</el-tag>
          <el-tag effect="light">Element Plus</el-tag>
          <el-tag effect="light">Pinia</el-tag>
          <el-tag effect="light">Flask</el-tag>
          <el-tag effect="light">Playwright</el-tag>
          <el-tag effect="light">SQLite</el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 关于页面组件
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.about {
  max-width: 820px;
  margin: 0 auto;

  .about-card {
    :deep(.el-card__body) {
      padding: 28px 32px;
    }

    .about-hero {
      display: flex;
      align-items: center;
      gap: 16px;

      .hero-icon {
        width: 52px;
        height: 52px;
        border-radius: 14px;
        background: linear-gradient(135deg, #4f46e5, #0ea5e9);
        color: #fff;
        font-weight: 800;
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 18px -4px rgba(79, 70, 229, 0.4);
        flex-shrink: 0;
      }

      h2 {
        color: $text-primary;
        margin: 0 0 4px 0;
        font-size: 20px;
        font-weight: 700;
      }

      .version {
        color: $text-secondary;
        font-size: 13px;
        margin: 0;
      }
    }

    .about-section {
      margin-bottom: 24px;

      &:last-child {
        margin-bottom: 0;
      }

      h3 {
        font-size: 15px;
        font-weight: 600;
        color: $text-primary;
        margin: 0 0 12px 0;
      }

      p {
        color: $text-regular;
        font-size: 14px;
        line-height: 1.8;
        margin: 0;
      }

      .platform-tags,
      .tech-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .plat-pill {
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 600;

        &.douyin { background: #fff1f2; color: #be123c; }
        &.kuaishou { background: #fff7ed; color: #c2410c; }
        &.channels { background: #fffbeb; color: #b45309; }
        &.xhs { background: #fdf2f8; color: #db2777; }
      }

      .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 10px;

        .feature-item {
          padding: 11px 14px;
          border-radius: 10px;
          background: #f8fafc;
          border: 1px solid $border-lighter;
          color: $text-regular;
          font-size: 13px;
          font-weight: 500;
        }
      }
    }
  }
}
</style>
