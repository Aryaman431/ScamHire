import { useEffect, useRef, useState } from "react";

type StackedPageProps = {
  children: React.ReactNode;
  className?: string;
  tone?: "dark" | "light" | "lime" | "ink";
  index: number;
};

export default function StackedPage({ children, className = "", tone = "dark", index }: StackedPageProps) {
  const ref = useRef<HTMLElement>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      const bounds = node.getBoundingClientRect();
      const travel = Math.max(window.innerHeight, bounds.height);
      const nextProgress = Math.min(1, Math.max(0, -bounds.top / travel));
      setProgress((current) => Math.abs(current - nextProgress) > 0.008 ? nextProgress : current);
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  const scale = 1 - progress * 0.045;
  const opacity = 1 - progress * 0.22;
  const translateY = progress * -12;
  const enterY = (1 - progress) * 18;

  return (
    <section
      ref={ref}
      className={`stacked-page stacked-page-${tone} ${className}`}
      style={{ "--stack-scale": scale, "--stack-opacity": opacity, "--stack-y": `${translateY}px`, "--stack-enter": `${enterY}vh`, "--stack-index": index } as React.CSSProperties}
    >
      <div className="stacked-page-frame">{children}</div>
    </section>
  );
}
