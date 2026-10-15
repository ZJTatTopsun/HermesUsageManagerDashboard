import type { ReactNode } from 'react';
import { React } from '../platform/react-host';

export function MaterialIcon({ name }: { name: string }) {
  return <span className="hum-material-icon" aria-hidden="true">{name}</span>;
}

export function InfoTip({ label, children }: { label: string; children: ReactNode }) {
  const element = React.useRef<HTMLDetailsElement>(null);
  React.useEffect(() => {
    const closeOutside = (event: PointerEvent) => {
      if (event.target instanceof Node && element.current && !element.current.contains(event.target)) element.current.open = false;
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && element.current?.open) {
        element.current.open = false;
        element.current.querySelector('summary')?.focus();
      }
    };
    document.addEventListener('pointerdown', closeOutside);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', closeOutside); document.removeEventListener('keydown', escape); };
  }, []);
  function alignPanel() {
    const anchor = element.current;
    const panel = anchor?.querySelector<HTMLElement>('.hum-info-panel');
    if (!anchor || !panel) return;
    const bounds = anchor.getBoundingClientRect();
    const width = Number.parseFloat(getComputedStyle(panel).width);
    const left = Math.max(16, Math.min(bounds.left, window.innerWidth - width - 16));
    panel.style.left = `${left - bounds.left}px`;
    panel.style.right = 'auto';
  }
  return <details ref={element} className="hum-info" onToggle={alignPanel}><summary aria-label={label} onClick={alignPanel}><MaterialIcon name="info" /></summary><div className="hum-info-panel">{children}</div></details>;
}
