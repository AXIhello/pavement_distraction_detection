<template>
  <div class="detail-view">
    <button @click="$emit('back')" class="detail-back-btn">← 返回列表</button>
    <h2>路障告警详情</h2>

    <div v-if="detail">
      <p><strong>视频ID：</strong>{{ detail.id }}</p>
      <p><strong>告警时间：</strong>{{ detail.created_at }}</p>
      <p><strong>状态：</strong>{{ detail.status }}</p>
      <p><strong>病害类型：</strong>{{ detail.disease_type }}</p>
      <p><strong>描述：</strong>{{ detail.description || '暂无描述' }}</p>
      <div v-if="detail.image_url">
        <img :src="detail.image_url" alt="告警图片" class="alert-image" />
      </div>
    </div>

    <div v-else>
      <p>正在加载详情...</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  detail: Object
})

defineEmits(['back'])
</script>

<style scoped>
.detail-view {
  padding: 24px;
  background-color: #f9fafb;
  border-radius: 12px;
}

.detail-back-btn {
  margin-bottom: 16px;
  padding: 8px 12px;
  font-size: 14px;
  background-color: #374151;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.alert-image {
  max-width: 400px;
  margin-top: 16px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
</style>
