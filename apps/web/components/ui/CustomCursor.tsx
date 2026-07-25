"use client";

import { useEffect } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";

export default function CustomCursor() {
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);

  const dotX = useSpring(cursorX, { stiffness: 600, damping: 35, mass: 0.2 });
  const dotY = useSpring(cursorY, { stiffness: 600, damping: 35, mass: 0.2 });

  const ringX = useSpring(cursorX, { stiffness: 250, damping: 28, mass: 0.5 });
  const ringY = useSpring(cursorY, { stiffness: 250, damping: 28, mass: 0.5 });

  useEffect(() => {
    const move = (e: MouseEvent) => {
      cursorX.set(e.clientX);
      cursorY.set(e.clientY);
    };
    window.addEventListener("mousemove", move);
    return () => window.removeEventListener("mousemove", move);
  }, [cursorX, cursorY]);

  return (
    <>
      <motion.div
        className="pointer-events-none fixed z-[9999]"
        style={{ left: ringX, top: ringY }}
      >
        <div
          className="relative -left-[18px] -top-[18px] h-9 w-9 rounded-full"
          style={{
            border: "1px solid rgba(96, 165, 250, 0.35)",
            background: "rgba(59, 130, 246, 0.04)",
            boxShadow:
              "0 0 24px rgba(59, 130, 246, 0.15), inset 0 0 20px rgba(59, 130, 246, 0.03)",
          }}
        />
      </motion.div>
      <motion.div
        className="pointer-events-none fixed z-[9999]"
        style={{ left: dotX, top: dotY }}
      >
        <div
          className="relative -left-[3px] -top-[3px] h-1.5 w-1.5 rounded-full"
          style={{
            background: "#f9fafb",
            boxShadow:
              "0 0 6px rgba(96, 165, 250, 0.7), 0 0 20px rgba(59, 130, 246, 0.3)",
          }}
        />
      </motion.div>
    </>
  );
}
