import streamlit as st
import time
import os
from datetime import datetime

st.set_page_config(page_title="Auto Capture", layout="centered")

# 保存フォルダ
SAVE_DIR = "captures"
os.makedirs(SAVE_DIR, exist_ok=True)

st.title("📸 自動撮影アプリ")

# フロントカメラから自動撮影する処理
js_code = """
<script>
let video = document.createElement('video');
video.setAttribute("autoplay", "");
video.setAttribute("playsinline", "");
video.style.width = "100%";
document.body.appendChild(video);

navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => { video.srcObject = stream });

function captureFrame() {
  let canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  let ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0);
  return canvas.toDataURL('image/png');
}

async function autoCapture() {
  for (let i = 0; i < 5; i++) {  // 5枚自動撮影
    let data = captureFrame();
    await fetch('/upload', {
      method: 'POST',
      body: data
    });
    await new Promise(r => setTimeout(r, 2000)); // 2秒間隔
  }
}
autoCapture();
</script>
"""

# JS を HTML に埋め込み
st.components.v1.html(js_code, height=0)

st.success("カメラ起動中... 自動で5枚撮影して保存されます。")

# 受信処理（Streamlit でフック）
if "images" not in st.session_state:
    st.session_state["images"] = []

from streamlit.server.server import Server
from tornado.web import RequestHandler

class UploadHandler(RequestHandler):
    def post(self):
        data_url = self.request.body.decode("utf-8")
        if data_url.startswith("data:image"):
            img_data = data_url.split(",")[1]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{SAVE_DIR}/capture_{ts}.png"
            with open(path, "wb") as f:
                f.write(bytes(img_data, "utf-8"))
            st.session_state["images"].append(path)

# Tornado にルート追加
server = Server.get_current()
if not any(r.regex.pattern == "/upload" for r in server._tornado.application.wildcard_router.rules):
    server._tornado.application.add_handlers(".*$", [(r"/upload", UploadHandler)])

# 保存済み画像一覧
if st.session_state["images"]:
    st.subheader("保存済みの画像")
    for img_path in st.session_state["images"]:
        st.image(img_path, caption=img_path)
