import { useEffect, useMemo, useRef } from "preact/hooks";
import uPlot from "uplot";

import type { RuntimeSample } from "./types";

type Props = {
  title: string;
  seriesLabel: string;
  samples: RuntimeSample[];
  readValue: (sample: RuntimeSample) => number | null | undefined;
};

export function MetricChart({ title, seriesLabel, samples, readValue }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<uPlot | null>(null);

  const data = useMemo(() => {
    const xs: number[] = [];
    const ys: number[] = [];
    for (const sample of samples) {
      const value = readValue(sample);
      if (value == null) {
        continue;
      }
      xs.push(Math.floor(new Date(sample.ts).getTime() / 1000));
      ys.push(value);
    }
    return [xs, ys];
  }, [samples, readValue]);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    if (data[0].length === 0) {
      return;
    }

    chartRef.current = new uPlot(
      {
        width: Math.max(containerRef.current.clientWidth, 320),
        height: 220,
        padding: [12, 8, 8, 8],
        legend: { show: false },
        scales: { x: { time: true } },
        series: [
          {},
          {
            label: seriesLabel,
            stroke: "#c35428",
            width: 2,
            points: { show: false },
          },
        ],
        axes: [
          {
            stroke: "#8d7f68",
            grid: { stroke: "#eadfcf" },
          },
          {
            stroke: "#8d7f68",
            grid: { stroke: "#eadfcf" },
          },
        ],
      },
      data,
      containerRef.current
    );

    return () => {
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, [data, seriesLabel]);

  return (
    <article class="chart-card">
      <div class="chart-head">
        <h3>{title}</h3>
        <span>{data[1].length ? data[1][data[1].length - 1] : "Unavailable"}</span>
      </div>
      {data[0].length ? (
        <div ref={containerRef} />
      ) : (
        <div class="chart-empty">No samples for this metric yet.</div>
      )}
    </article>
  );
}
