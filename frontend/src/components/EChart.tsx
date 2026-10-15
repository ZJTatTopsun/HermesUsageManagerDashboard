import { init, use, type EChartsType } from 'echarts/core';
import { BarChart, LineChart, PieChart } from 'echarts/charts';
import { AriaComponent, DataZoomComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
import { LabelLayout } from 'echarts/features';
import type { EChartsOption } from 'echarts';
import { React } from '../platform/react-host';

use([BarChart, LineChart, PieChart, AriaComponent, DataZoomComponent, GridComponent, LegendComponent, TooltipComponent, SVGRenderer, LabelLayout]);
export type ChartOption = EChartsOption;
export type ChartClick = { name: string; dataIndex: number; seriesName: string };

export function EChart({ option, label, height = 300, onClick }: { option: ChartOption; label: string; height?: number; onClick?: (event: ChartClick) => void }) {
  const container = React.useRef<HTMLDivElement>(null);
  const chart = React.useRef<EChartsType | null>(null);
  const callback = React.useRef(onClick);
  callback.current = onClick;
  React.useEffect(() => {
    const node = container.current;
    if (!node) return;
    const instance = init(node, undefined, { renderer: 'svg' });
    chart.current = instance;
    const observer = new ResizeObserver(() => { if (!instance.isDisposed()) instance.resize(); });
    observer.observe(node);
    instance.on('click', (event) => callback.current?.(event as ChartClick));
    return () => { observer.disconnect(); instance.off('click'); instance.dispose(); chart.current = null; };
  }, []);
  React.useEffect(() => {
    chart.current?.setOption({ ...option, animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches, animationDuration: 250, aria: { enabled: true } }, { notMerge: true });
  }, [option]);
  return <div ref={container} className="hum-chart" role="img" aria-label={label} style={{ height }} />;
}
