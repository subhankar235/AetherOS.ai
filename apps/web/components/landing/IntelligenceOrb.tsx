"use client";

import { useRef, useEffect } from "react";

interface Particle {
  angle: number;
  baseRadius: number;
  speed: number;
  size: number;
  opacity: number;
  driftPhase: number;
  driftAmp: number;
  driftSpeed: number;
}

interface IncomingParticle {
  progress: number;
  speed: number;
  angle: number;
  size: number;
}

export default function IntelligenceOrb() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -9999, y: -9999 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let animationId: number;
    let time = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const ro = new ResizeObserver(() => resize());
    ro.observe(canvas);

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };
    const handleMouseLeave = () => {
      mouseRef.current = { x: -9999, y: -9999 };
    };
    window.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseleave", handleMouseLeave);

    const particles: Particle[] = [];
    const numParticles = 70;
    for (let i = 0; i < numParticles; i++) {
      const angle = (i / numParticles) * Math.PI * 2;
      const radius = 120 + Math.random() * 220;
      particles.push({
        angle,
        baseRadius: radius,
        speed: 0.0002 + Math.random() * 0.0006,
        size: 0.5 + Math.random() * 1.8,
        opacity: 0.15 + Math.random() * 0.4,
        driftPhase: Math.random() * Math.PI * 2,
        driftAmp: 15 + Math.random() * 35,
        driftSpeed: 0.3 + Math.random() * 0.7,
      });
    }

    const incoming: IncomingParticle[] = [];
    for (let i = 0; i < 8; i++) {
      incoming.push({
        progress: Math.random(),
        speed: 0.001 + Math.random() * 0.002,
        angle: Math.random() * Math.PI * 2,
        size: 1 + Math.random() * 1.5,
      });
    }

    const draw = () => {
      time += 0.008;
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      const cx = w / 2;
      const cy = h / 2;

      ctx.fillStyle = "rgba(5, 5, 5, 0.12)";
      ctx.fillRect(0, 0, w, h);

      const pulse = Math.sin(time * 0.8) * 0.5 + 0.5;
      const orbRadius = 70 + pulse * 15;

      const ambient = ctx.createRadialGradient(cx, cy, 0, cx, cy, orbRadius * 4);
      ambient.addColorStop(0, `rgba(59, 130, 246, ${0.08 + pulse * 0.05})`);
      ambient.addColorStop(0.3, "rgba(59, 130, 246, 0.03)");
      ambient.addColorStop(1, "rgba(59, 130, 246, 0)");
      ctx.fillStyle = ambient;
      ctx.fillRect(0, 0, w, h);

      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, orbRadius);
      core.addColorStop(0, `rgba(96, 165, 250, ${0.25 + pulse * 0.15})`);
      core.addColorStop(0.4, "rgba(59, 130, 246, 0.08)");
      core.addColorStop(1, "rgba(59, 130, 246, 0)");
      ctx.fillStyle = core;
      ctx.beginPath();
      ctx.arc(cx, cy, orbRadius, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, orbRadius * 0.6, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(96, 165, 250, ${0.15 + pulse * 0.1})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      particles.forEach((p) => {
        p.angle += p.speed;
        const drift = Math.sin(time * p.driftSpeed + p.driftPhase) * p.driftAmp;
        const r = p.baseRadius + drift;
        const px = cx + Math.cos(p.angle) * r;
        const py = cy + Math.sin(p.angle) * r;

        const dx = px - mouseRef.current.x;
        const dy = py - mouseRef.current.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const influence = Math.max(0, 1 - dist / 180);

        const size = p.size + influence * 2.5;
        const opacity = Math.min(1, p.opacity + influence * 0.4);

        ctx.beginPath();
        ctx.arc(px, py, size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(96, 165, 250, ${opacity})`;
        ctx.fill();

        if (r < 260) {
          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(cx, cy);
          ctx.strokeStyle = `rgba(59, 130, 246, ${opacity * 0.04})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      });

      incoming.forEach((p) => {
        p.progress += p.speed;
        if (p.progress >= 1) {
          p.progress = 0;
          p.angle = Math.random() * Math.PI * 2;
        }
        const r = (1 - p.progress) * Math.max(w, h) * 0.5;
        const px = cx + Math.cos(p.angle) * r;
        const py = cy + Math.sin(p.angle) * r;
        const fadeOpacity = p.progress * 0.5;

        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(96, 165, 250, ${fadeOpacity})`;
        ctx.fill();

        const trailGrad = ctx.createLinearGradient(px, py, cx, cy);
        trailGrad.addColorStop(0, `rgba(96, 165, 250, ${fadeOpacity * 0.3})`);
        trailGrad.addColorStop(1, "rgba(96, 165, 250, 0)");
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(cx, cy);
        ctx.strokeStyle = trailGrad;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      });

      animationId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(animationId);
      ro.disconnect();
      window.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  return <canvas ref={canvasRef} className="w-full h-full" aria-hidden="true" />;
}
