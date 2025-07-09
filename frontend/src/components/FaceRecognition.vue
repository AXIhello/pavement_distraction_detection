<template>
  <div class="face-camera">
    <h2>人脸识别</h2>
    <div class="video-container">
      <video ref="video" autoplay playsinline></video>
    </div>
    <button @click="startCamera">开启摄像头识别</button>
    <p class="tip">请正对摄像头，系统将自动识别您的人脸</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { io } from 'socket.io-client'

const router = useRouter()

const video = ref(null)
let socket = null
let streamInterval = null
let stream = null
async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream

    // 连接 SocketIO
    socket = io('http://127.0.0.1:8000')

    socket.on('connect', () => {
      console.log('SocketIO 连接成功');

      startImageStream()
    });


    socket.on('face_result', (result) => {
      console.log('识别结果:', result);


      if (result.success) {
        const face = result.faces[0];
        if (face.name === '陌生人') {
          alert('告警：检测到陌生人！');
      // 停止摄像头 & 关闭 SocketIO
          clearInterval(streamInterval)
          stream.getTracks().forEach(track => track.stop())
          socket.disconnect()
      // 跳转到登录界面
          router.push('/login')
          return;
    }
        console.log('识别成功:', result.faces);
        // 停止摄像头 & 关闭 SocketIO
        clearInterval(streamInterval)
        stream.getTracks().forEach(track => track.stop())
        socket.disconnect()

        // 跳转到首页
        router.push('/home')
      } else {
        console.log('识别结果:', result.message);
      }
    });

    socket.on('disconnect', () => {
      console.log('SocketIO 连接断开');
      clearInterval(streamInterval)
    });

    socket.on('connect_error', (error) => {
      console.error('SocketIO 连接错误:', error);
      clearInterval(streamInterval)
    });

  } catch (err) {
    alert('无法访问摄像头：' + err.message)
  }
}

function startImageStream() {
  video.value.onloadedmetadata = () => {
    console.log('视频元数据加载完成，开始发送图像流')
    streamInterval = setInterval(() => {
      if (video.value.videoWidth === 0 || video.value.videoHeight === 0) {
        console.error('摄像头未正确初始化')
        return
      }
      const canvas = document.createElement('canvas')
      canvas.width = video.value.videoWidth
      canvas.height = video.value.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)
      const base64Image = canvas.toDataURL('image/jpeg')
      socket.emit('face_recognition', { image: base64Image })
    }, 200)
  }
}


</script>

<style scoped>
.face-camera {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  font-family: "Arial", sans-serif;
  background-color: #f9f9f9;
  border-radius: 16px;
  max-width: 480px;
  margin: 60px auto;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.face-camera h2 {
  font-size: 28px;
  margin-bottom: 24px;
  color: #333;
}

.video-container {
  width: 100%;
  aspect-ratio: 4/3;
  background-color: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

button {
  margin-top: 20px;
  padding: 12px 24px;
  font-size: 16px;
  border: none;
  background-color: #d7c480;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background-color: #005fcc;
}

.tip {
  margin-top: 16px;
  font-size: 14px;
  color: #666;
}
</style>
