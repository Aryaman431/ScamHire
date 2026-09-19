import { Children, useEffect, useRef, useState } from "react";

type PageStackProps = {
  children: React.ReactNode;
  className?: string;
};

type PageStackState = {
  active: number;
  next: number | null;
  direction: 1 | -1;
  progress: number;
};

const TRANSITION_MS = 560;
const WHEEL_THRESHOLD = 18;

export default function PageStack({ children, className = "" }: PageStackProps) {
  const pages = Children.toArray(children);
  const [enhanced, setEnhanced] = useState(false);
  const [stack, setStack] = useState<PageStackState>({ active: 0, next: null, direction: 1, progress: 0 });
  const stackRef = useRef(stack);
  const lockedRef = useRef(false);
  const wheelAccumulator = useRef(0);
  const animationFrame = useRef<number | null>(null);
  const touchStart = useRef<number | null>(null);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    document.documentElement.classList.toggle("page-stack-active", !reduced && finePointer);
    setEnhanced(!reduced && finePointer);
    return () => document.documentElement.classList.remove("page-stack-active");
  }, []);

  useEffect(() => {
    stackRef.current = stack;
  }, [stack]);

  useEffect(() => {
    if (!enhanced || pages.length < 2) return;

    const finish = (target: number) => {
      setStack({ active: target, next: null, direction: 1, progress: 0 });
      lockedRef.current = false;
      wheelAccumulator.current = 0;
    };

    const animateTo = (target: number, duration = TRANSITION_MS) => {
      const current = stackRef.current;
      if (lockedRef.current) return;
      if (target < 0 || target >= pages.length || target === current.active) return;
      const direction = target > current.active ? 1 : -1;
      lockedRef.current = true;
      const started = performance.now();
      setStack({ active: current.active, next: target, direction, progress: 0 });

      const tick = (now: number) => {
        const raw = Math.min(1, (now - started) / duration);
        const eased = 1 - Math.pow(1 - raw, 3);
        setStack({ active: current.active, next: target, direction, progress: eased });
        if (raw < 1) {
          animationFrame.current = window.requestAnimationFrame(tick);
        } else {
          finish(target);
        }
      };
      animationFrame.current = window.requestAnimationFrame(tick);
    };

    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      if (lockedRef.current) return;
      wheelAccumulator.current += event.deltaY;
      if (Math.abs(wheelAccumulator.current) < WHEEL_THRESHOLD) return;
      animateTo(stackRef.current.active + (wheelAccumulator.current > 0 ? 1 : -1));
    };

    const onKeyDown = (event: KeyboardEvent) => {
      const nextKeys = ["ArrowDown", "PageDown", " "];
      const previousKeys = ["ArrowUp", "PageUp"];
      if (![...nextKeys, ...previousKeys].includes(event.key)) return;
      event.preventDefault();
      animateTo(stackRef.current.active + (nextKeys.includes(event.key) ? 1 : -1));
    };

    const onTouchStart = (event: TouchEvent) => {
      touchStart.current = event.touches[0]?.clientY ?? null;
    };
    const onTouchEnd = (event: TouchEvent) => {
      if (touchStart.current === null) return;
      const end = event.changedTouches[0]?.clientY ?? touchStart.current;
      const delta = touchStart.current - end;
      touchStart.current = null;
      if (Math.abs(delta) > 42) animateTo(stackRef.current.active + (delta > 0 ? 1 : -1));
    };
    const onNavigate = (event: Event) => {
      const target = (event as CustomEvent<number>).detail;
      if (typeof target === "number") animateTo(target, 400);
    };

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchend", onTouchEnd, { passive: true });
    window.addEventListener("page-stack:navigate", onNavigate);
    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchend", onTouchEnd);
      window.removeEventListener("page-stack:navigate", onNavigate);
      if (animationFrame.current) window.cancelAnimationFrame(animationFrame.current);
    };
  }, [enhanced, pages.length]);

  if (!enhanced) {
    return <div className={`page-stack page-stack-normal ${className}`}>{pages.map((page, index) => <div className="page-stack-normal-page" key={index}>{page}</div>)}</div>;
  }

  const current = stack.active;
  const incoming = stack.next;
  const progress = stack.progress;
  const outgoingStyle = { transform: `scale(${1 - progress * 0.06})`, opacity: 1 - progress * 0.75 };
  const incomingStyle = incoming === null ? undefined : { transform: `translate3d(0, ${stack.direction * (1 - progress) * 100}%, 0)` };

  return (
    <div className={`page-stack ${className}`} aria-live="polite">
      <div className="page-stack-viewport">
        {pages.map((page, index) => {
          const isCurrent = index === current;
          const isIncoming = index === incoming;
          const style = isIncoming ? incomingStyle : isCurrent ? outgoingStyle : undefined;
          return <div className={`page-stack-layer ${isCurrent ? "is-current" : ""} ${isIncoming ? "is-incoming" : ""}`} style={style} aria-hidden={!isCurrent && !isIncoming} key={index}>{page}</div>;
        })}
      </div>
      <div className="page-stack-progress" aria-hidden="true"><span style={{ transform: `scaleX(${(current + (incoming === null ? 0 : progress)) / Math.max(1, pages.length - 1)})` }} /></div>
    </div>
  );
}
