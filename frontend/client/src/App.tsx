import { useEffect, useRef, useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import History from "./pages/History";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";

function CursorPulse() {
  const cursorRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const burstTimer = useRef<number | undefined>(undefined);

  useEffect(() => {
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    if (!finePointer) return;
    const cursor = cursorRef.current;
    if (!cursor) return;

    const onMove = (event: PointerEvent) => {
      setVisible(true);
      cursor.style.transform = `translate3d(${event.clientX}px, ${event.clientY}px, 0)`;
      let node = document.elementFromPoint(event.clientX, event.clientY) as HTMLElement | null;
      let background = "";
      while (node && !background) {
        const candidate = window.getComputedStyle(node).backgroundColor;
        if (candidate && candidate !== "rgba(0, 0, 0, 0)" && candidate !== "transparent") background = candidate;
        node = node.parentElement;
      }
      const values = background.match(/[\d.]+/g)?.map(Number) ?? [16, 18, 18];
      const [red, green, blue] = values;
      const luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;
      cursor.style.setProperty("--cursor-color", luminance > 0.56 ? "#101212" : "#f0eee8");
    };
    const onLeave = () => setVisible(false);
    const onDown = () => {
      cursor.classList.remove("cursor-burst");
      void cursor.offsetWidth;
      cursor.classList.add("cursor-burst");
      window.clearTimeout(burstTimer.current);
      burstTimer.current = window.setTimeout(() => cursor.classList.remove("cursor-burst"), 850);
    };

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerleave", onLeave);
    window.addEventListener("pointerdown", onDown);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("pointerdown", onDown);
      window.clearTimeout(burstTimer.current);
    };
  }, []);

  return <div ref={cursorRef} className={`custom-cursor ${visible ? "is-visible" : ""}`} aria-hidden="true" />;
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/history" component={History} />
      <Route path="/privacy" component={Privacy} />
      <Route path="/terms" component={Terms} />
      <Route component={Home} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <Toaster />
          <CursorPulse />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
