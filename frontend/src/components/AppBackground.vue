<template>
  <div class="bg-scene" aria-hidden="true">
    <div class="bg-photo" />
    <div class="bg-texture" />
    <div class="bg-mesh" />
    <div class="bg-grid" />
    <div class="bg-vignette" />
    <div class="orb orb-a" />
    <div class="orb orb-b" />
    <div class="orb orb-c" />
    <div class="beam beam-left" />
    <div class="beam beam-right" />
    <div class="particles">
      <span v-for="n in 18" :key="n" class="particle" :style="{ '--p': n }" />
    </div>
  </div>
</template>

<style scoped>
.bg-scene {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
  background: var(--bg);
}

.bg-photo {
  position: absolute;
  inset: 0;
  background:
    url('/images/hero-ceremony-bg.png') center top / cover no-repeat;
  opacity: 0.22;
  transform: scale(1.04);
  animation: slowZoom 30s ease-in-out infinite alternate;
}

.bg-texture {
  position: absolute;
  inset: 0;
  background: url('/images/bg-texture.png') center / cover no-repeat;
  opacity: 0.35;
  mix-blend-mode: screen;
}

.bg-mesh {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(74, 222, 128, 0.12), transparent 55%),
    radial-gradient(ellipse 60% 40% at 90% 10%, rgba(245, 197, 66, 0.08), transparent 50%),
    radial-gradient(ellipse 50% 35% at 50% 100%, rgba(56, 189, 248, 0.06), transparent 55%),
    linear-gradient(180deg, rgba(6, 10, 16, 0.55) 0%, rgba(10, 16, 25, 0.75) 45%, rgba(7, 11, 18, 0.92) 100%);
}

.bg-vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 70% at 50% 40%, transparent 30%, rgba(4, 8, 14, 0.75) 100%);
  pointer-events: none;
}

.bg-grid {
  position: absolute;
  inset: 0;
  opacity: 0.28;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 30%, black, transparent);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  animation: float 18s ease-in-out infinite;
}

.orb-a {
  width: 420px;
  height: 420px;
  top: -120px;
  left: -80px;
  background: rgba(74, 222, 128, 0.1);
}

.orb-b {
  width: 360px;
  height: 360px;
  top: 20%;
  right: -100px;
  background: rgba(245, 197, 66, 0.08);
  animation-delay: -6s;
}

.orb-c {
  width: 300px;
  height: 300px;
  bottom: -80px;
  left: 35%;
  background: rgba(56, 189, 248, 0.06);
  animation-delay: -12s;
}

.beam {
  position: absolute;
  top: 0;
  width: 280px;
  height: 100%;
  opacity: 0.05;
  background: linear-gradient(180deg, rgba(245, 197, 66, 0.5), transparent 70%);
  transform-origin: top center;
  animation: sweep 12s ease-in-out infinite;
}

.beam-left {
  left: 15%;
  transform: rotate(-12deg);
}

.beam-right {
  right: 12%;
  transform: rotate(12deg);
  animation-delay: -6s;
}

.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(245, 197, 66, 0.55);
  left: calc((var(--p) * 5.5%) + 2%);
  top: calc((var(--p) * 4.3%) + 5%);
  animation: drift 14s ease-in-out infinite;
  animation-delay: calc(var(--p) * -0.7s);
  opacity: 0.35;
}

.particle:nth-child(3n) {
  background: rgba(74, 222, 128, 0.5);
  width: 2px;
  height: 2px;
}

.particle:nth-child(5n) {
  width: 4px;
  height: 4px;
  opacity: 0.5;
}

@keyframes slowZoom {
  from { transform: scale(1.04); }
  to { transform: scale(1.08); }
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(24px, 16px) scale(1.05); }
  66% { transform: translate(-16px, 24px) scale(0.95); }
}

@keyframes sweep {
  0%, 100% { opacity: 0.03; }
  50% { opacity: 0.08; }
}

@keyframes drift {
  0%, 100% {
    transform: translate(0, 0);
    opacity: 0.2;
  }
  50% {
    transform: translate(12px, -28px);
    opacity: 0.65;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bg-photo,
  .orb,
  .beam,
  .particle {
    animation: none;
  }
}
</style>
