/*
 * The WebGL side of <ColorBends />: one full-screen fragment shader drawing animated color
 * bands. Ported from React Bits' ColorBends (https://reactbits.dev) to plain WebGL: the same
 * shader without three.js, which would add ~130 KB of JavaScript to the page. Loaded on
 * demand by components/color-bends.tsx, so none of it is in the page's first download.
 */

const MAX_COLORS = 8;
// The bands are soft, so half resolution looks the same for a quarter of the GPU work.
const RESOLUTION = 0.5;
// Slow-moving bands look the same at 30 frames per second, for half the work.
const FRAME_INTERVAL_MS = 1000 / 30;

const VERTEX_SHADER = `
attribute vec2 aPosition;
varying vec2 vUv;
void main() {
  vUv = aPosition * 0.5 + 0.5;
  gl_Position = vec4(aPosition, 0.0, 1.0);
}`;

const FRAGMENT_SHADER = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
#define MAX_COLORS ${MAX_COLORS}
uniform vec2 uCanvas;
uniform float uTime;
uniform float uSpeed;
uniform vec2 uRot;
uniform int uColorCount;
uniform vec3 uColors[MAX_COLORS];
uniform float uScale;
uniform float uFrequency;
uniform float uWarpStrength;
uniform vec2 uPointer;
uniform float uMouseInfluence;
uniform float uParallax;
uniform float uNoise;
uniform int uIterations;
uniform float uIntensity;
uniform float uBandWidth;
varying vec2 vUv;

void main() {
  float t = uTime * uSpeed;
  vec2 p = vUv * 2.0 - 1.0;
  p += uPointer * uParallax * 0.1;
  vec2 rp = vec2(p.x * uRot.x - p.y * uRot.y, p.x * uRot.y + p.y * uRot.x);
  vec2 q = vec2(rp.x * (uCanvas.x / uCanvas.y), rp.y);
  q /= max(uScale, 0.0001);
  q /= 0.5 + 0.2 * dot(q, q);
  q += 0.2 * cos(t) - 7.56;
  vec2 shift = vec2(0.2 * cos(t) - 7.56);
  q += (uPointer - rp) * uMouseInfluence * 0.2;

  for (int j = 0; j < 5; j++) {
    if (j >= uIterations - 1) break;
    vec2 rr = sin(1.5 * (q.yx * uFrequency) + 2.0 * cos(q * uFrequency));
    q += (rr - q) * 0.15;
    shift *= 0.85;
  }

  vec2 s = q;
  vec3 sumCol = vec3(0.0);
  float cover = 0.0;
  float kBelow = clamp(uWarpStrength, 0.0, 1.0);
  float kMix = pow(kBelow, 0.3);
  float gain = 1.0 + max(uWarpStrength - 1.0, 0.0);
  for (int i = 0; i < MAX_COLORS; ++i) {
    if (i >= uColorCount) break;
    s -= 0.01;
    vec2 r = sin(1.5 * (s.yx * uFrequency) + 2.0 * cos(s * uFrequency));
    float m0 = length(r + sin(5.0 * r.y * uFrequency - 3.0 * t + float(i)) / 4.0);
    vec2 warped = s + (r - s) * kBelow * gain;
    float spare = 1.0 - kBelow * gain;
    if (spare != 0.0) warped -= shift * spare;
    float m1 = length(warped + sin(5.0 * warped.y * uFrequency - 3.0 * t + float(i)) / 4.0);
    float m = mix(m0, m1, kMix);
    float w = 1.0 - exp(-uBandWidth / exp(uBandWidth * m));
    sumCol += uColors[i] * w;
    cover = max(cover, w);
  }
  vec3 col = clamp(sumCol, 0.0, 1.0) * uIntensity;

  if (uNoise > 0.0001) {
    float n = fract(sin(dot(gl_FragCoord.xy + vec2(uTime), vec2(12.9898, 78.233))) * 43758.5453123);
    col = clamp(col + (n - 0.5) * uNoise, 0.0, 1.0);
  }

  // Premultiplied alpha: the page background shows wherever no band covers it.
  gl_FragColor = vec4(col * cover, cover);
}`;

const UNIFORMS = [
  "uCanvas",
  "uTime",
  "uSpeed",
  "uRot",
  "uColorCount",
  "uColors",
  "uScale",
  "uFrequency",
  "uWarpStrength",
  "uPointer",
  "uMouseInfluence",
  "uParallax",
  "uNoise",
  "uIterations",
  "uIntensity",
  "uBandWidth",
] as const;

type Uniform = (typeof UNIFORMS)[number];

export type ColorBendsSettings = {
  rotation: number;
  autoRotate: number;
  speed: number;
  scale: number;
  frequency: number;
  warpStrength: number;
  mouseInfluence: number;
  parallax: number;
  noise: number;
  iterations: number;
  intensity: number;
  bandWidth: number;
};

/** Read on every frame, so prop changes apply without restarting WebGL. */
export type ColorBendsSource = {
  settings: () => ColorBendsSettings | null;
  colors: () => readonly string[];
};

function hexToRgb(hex: string): [number, number, number] {
  const digits = hex.replace("#", "").trim();
  const full = digits.length === 3 ? [...digits].map((digit) => digit + digit).join("") : digits;
  const value = Number.parseInt(full, 16);
  return [((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255];
}

/** Resolves theme variables against the element, so the bands follow the design tokens. */
function colorData(colors: readonly string[], element: Element): Float32Array {
  const styles = getComputedStyle(element);
  const data = new Float32Array(MAX_COLORS * 3);
  colors.slice(0, MAX_COLORS).forEach((color, index) => {
    const hex = color.startsWith("--") ? styles.getPropertyValue(color) : color;
    data.set(hexToRgb(hex), index * 3);
  });
  return data;
}

function compileShader(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) {
    return null;
  }
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error("ColorBends: the shader did not compile.", gl.getShaderInfoLog(shader));
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

function createProgram(gl: WebGLRenderingContext) {
  const vertex = compileShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER);
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
  const program = gl.createProgram();
  if (!vertex || !fragment || !program) {
    return null;
  }
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  gl.deleteShader(vertex);
  gl.deleteShader(fragment);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error("ColorBends: the shader program did not link.", gl.getProgramInfoLog(program));
    gl.deleteProgram(program);
    return null;
  }
  return program;
}

/**
 * Draws the bands on the canvas until the returned cleanup runs. Returns null without WebGL
 * (the canvas stays empty). With reduced motion it draws one still frame.
 */
export function startColorBends(
  canvas: HTMLCanvasElement,
  source: ColorBendsSource,
): (() => void) | null {
  const gl = canvas.getContext("webgl", {
    alpha: true,
    antialias: false,
    premultipliedAlpha: true,
    powerPreference: "low-power",
  });
  // A lost context (GPU reset, too many contexts) can't compile anything: show no bands.
  if (!gl || gl.isContextLost()) {
    return null;
  }
  const program = createProgram(gl);
  if (!program) {
    return null;
  }
  gl.useProgram(program);

  // One triangle that covers the whole canvas.
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const position = gl.getAttribLocation(program, "aPosition");
  gl.enableVertexAttribArray(position);
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

  const uniform = Object.fromEntries(
    UNIFORMS.map((name) => [name, gl.getUniformLocation(program, name)]),
  ) as Record<Uniform, WebGLUniformLocation | null>;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const pointerTarget = { x: 0, y: 0 };
  const pointer = { x: 0, y: 0 };
  let colors = source.colors();
  let palette = colorData(colors, canvas);
  let elapsed = 0;
  let lastFrame = 0;
  let frame = 0;
  let visible = true;

  const draw = () => {
    const settings = source.settings();
    if (!settings) {
      return;
    }
    if (source.colors() !== colors) {
      colors = source.colors();
      palette = colorData(colors, canvas);
    }
    const angle = ((settings.rotation % 360) + settings.autoRotate * elapsed) * (Math.PI / 180);
    gl.uniform2f(uniform.uCanvas, canvas.width, canvas.height);
    gl.uniform1f(uniform.uTime, elapsed);
    gl.uniform1f(uniform.uSpeed, settings.speed);
    gl.uniform2f(uniform.uRot, Math.cos(angle), Math.sin(angle));
    gl.uniform1i(uniform.uColorCount, Math.min(colors.length, MAX_COLORS));
    gl.uniform3fv(uniform.uColors, palette);
    gl.uniform1f(uniform.uScale, settings.scale);
    gl.uniform1f(uniform.uFrequency, settings.frequency);
    gl.uniform1f(uniform.uWarpStrength, settings.warpStrength);
    gl.uniform2f(uniform.uPointer, pointer.x, pointer.y);
    gl.uniform1f(uniform.uMouseInfluence, settings.mouseInfluence);
    gl.uniform1f(uniform.uParallax, settings.parallax);
    gl.uniform1f(uniform.uNoise, settings.noise);
    gl.uniform1i(uniform.uIterations, settings.iterations);
    gl.uniform1f(uniform.uIntensity, settings.intensity);
    gl.uniform1f(uniform.uBandWidth, settings.bandWidth);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };

  const loop = (now: number) => {
    frame = 0;
    if (!visible || document.hidden) {
      return;
    }
    frame = requestAnimationFrame(loop);
    if (lastFrame && now - lastFrame < FRAME_INTERVAL_MS) {
      return;
    }
    // Capped, so the bands don't jump after the tab or the section was hidden.
    const delta = lastFrame ? Math.min((now - lastFrame) / 1000, 0.1) : 0;
    lastFrame = now;
    elapsed += delta;
    const ease = Math.min(1, delta * 8);
    pointer.x += (pointerTarget.x - pointer.x) * ease;
    pointer.y += (pointerTarget.y - pointer.y) * ease;
    draw();
  };

  const resume = () => {
    if (reduceMotion || frame || !visible || document.hidden) {
      return;
    }
    lastFrame = 0;
    frame = requestAnimationFrame(loop);
  };

  const resize = () => {
    canvas.width = Math.max(1, Math.round(canvas.clientWidth * RESOLUTION));
    canvas.height = Math.max(1, Math.round(canvas.clientHeight * RESOLUTION));
    gl.viewport(0, 0, canvas.width, canvas.height);
    draw();
  };

  // On the window: the page content above the canvas would catch the pointer first.
  const trackPointer = (event: PointerEvent) => {
    const rect = canvas.getBoundingClientRect();
    pointerTarget.x = ((event.clientX - rect.left) / (rect.width || 1)) * 2 - 1;
    pointerTarget.y = -(((event.clientY - rect.top) / (rect.height || 1)) * 2 - 1);
  };

  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(canvas);
  const visibilityObserver = new IntersectionObserver((entries) => {
    visible = entries.some((entry) => entry.isIntersecting);
    resume();
  });
  visibilityObserver.observe(canvas);
  document.addEventListener("visibilitychange", resume);
  if (!reduceMotion) {
    window.addEventListener("pointermove", trackPointer, { passive: true });
  }

  resize();
  resume();

  return () => {
    cancelAnimationFrame(frame);
    resizeObserver.disconnect();
    visibilityObserver.disconnect();
    document.removeEventListener("visibilitychange", resume);
    window.removeEventListener("pointermove", trackPointer);
    gl.deleteBuffer(buffer);
    gl.deleteProgram(program);
    // The context is not force-lost here: Next.js keeps a visited page mounted but hidden,
    // and coming back restarts on this same canvas, which would get the dead context back.
    // The browser frees it with the canvas.
  };
}
