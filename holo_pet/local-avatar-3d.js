import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const canvas = document.querySelector("#avatar-canvas");
if (canvas) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(24, 1, 0.01, 100);
  camera.position.set(0, 1.35, 6.4);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;
  // ── IBL 环境（修 AI 味禁令 ❌「无环境光的纯方向光打光」）────────────────
  // 🔴 2026-09-25 修：原来这里**只有半球光 + 两盏方向光**（key 3.4 / rim 2.2 / hemi 2.4），
  //    没有任何环境贴图 ⇒ 皮肤只有方向光的镜面高光、**没有环境的漫反射包裹**，
  //    阴影死黑、整体像 CG。three.js 官方对 MeshPhysicalMaterial 的原话是
  //    "For best results, always specify an environment map"。
  //    RoomEnvironment 是**程序化**影棚环境（不依赖外部 HDRI 文件），离线可跑。
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 1.0;
  // 🔴 光照配比必须跟着压：环境已经承担绝大部分漫反射，方向光留原来的强度会叠爆
  //    （在离线取景器里实测过：黑衣冲成灰褐、皮肤惨白）。影棚口径 —— 主光负责形，
  //    辅光只提暗部，勾边给轮廓，半球光几乎只做底色。
  scene.add(new THREE.HemisphereLight(0xd9f8ff, 0x07101f, 0.30));
  const key = new THREE.DirectionalLight(0xffffff, 1.15);
  key.position.set(2, 4, 4);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x4fe7ff, 0.65);
  rim.position.set(-3, 2, -3);
  scene.add(rim);
  let model;
  let mixer;
  const loader = new GLTFLoader();
  // 🔴 2026-09-25 换代：从上一代的 `model-rigged-anim.glb`（3.22 MiB · 22 骨）
  //    换成**本代已过出厂闸的终件** `avatar-hd.glb`（54.35 MB · **26 关节** ·
  //    idle/talk 两段动画 · 头独占 3×4096² 贴图 · 资产级金属度 0 + T 区/唇部粗糙度差异）。
  //    换它的依据是可复核的读数（不是文件名）：
  //      ① 出厂闸 release-check.py 六组硬检全过；
  //      ② 自研绑骨（0 积分）22 关节 + 4 根头发弹簧链 = 26；
  //      ③ gltf.animations[0] 是 idle（4.0s · 首末帧逐位相等 = 可无缝循环）。
  //    ⚠️ 已知代价：**51 MB 比上一代重 16 倍**，面板首屏会明显变慢。
  //       变轻需要减面，而本地两条减面路已独立验证**全部毁 UV** ⇒ 需服务端或 DCC（待 Owner 定）。
  loader.load("./assets/digital-human/raw/rig/avatar-hd.glb", (gltf) => {
    model = gltf.scene;
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    model.position.sub(center);
    model.position.y = -size.y * 0.34;
    model.rotation.y = Math.PI;
    const scale = 1.65 / Math.max(size.y, 0.01);
    model.scale.setScalar(scale);
    scene.add(model);
    if (gltf.animations.length) {
      mixer = new THREE.AnimationMixer(model);
      mixer.clipAction(gltf.animations[0]).play();
    }
    document.body.dataset.localAvatar3d = "ready";
    console.log("[local-avatar-3d] loaded", JSON.stringify({ animations: gltf.animations.length, height: size.y, scale }));
  }, undefined, (error) => {
    document.body.dataset.localAvatar3d = "failed";
    const reason = document.querySelector("#fallback-reason");
    if (reason) reason.textContent = "本地三维模型加载失败";
    console.error("[local-avatar-3d] GLB load failed", error);
  });
  const clock = new THREE.Clock();
  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    const width = Math.max(1, rect.width);
    const height = Math.max(1, rect.height - 80);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(canvas.parentElement);
  resize();
  function frame() {
    const elapsed = clock.getElapsedTime();
    if (mixer) mixer.update(Math.min(clock.getDelta(), 0.05));
    if (model) {
      model.rotation.y = Math.sin(elapsed * 0.42) * 0.045;
      model.position.x = Math.sin(elapsed * 0.8) * 0.015;
    }
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  frame();
}
