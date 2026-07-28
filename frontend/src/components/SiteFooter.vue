<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <span>© {{ year }} · xiaobawang001</span>
      <span class="footer-sep">·</span>
      <span>Powered by Notes</span>
    </div>
  </footer>
</template>

<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<style scoped>
.site-footer {
  border-top: 1px solid var(--yuque-border-light);
  background: var(--yuque-paper-bg);
  padding: 20px 0;
  margin-top: 40px;
  text-align: center;
}
.footer-inner {
  font-size: 13px;
  color: var(--yuque-text-secondary);
}
.footer-sep {
  margin: 0 8px;
  color: var(--yuque-border);
}
</style>
