"use client";

import { useEffect, useRef, useState } from "react";
import { api, ScanEvent, wsBase } from "@/lib/api";

export default function LiveEventFeed({ scanId }: { scanId: string }) {
  const [events, setEvents] = useState<ScanEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const seenIds = useRef<Set<string>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);

  function addEvents(newEvents: ScanEvent[]) {
    setEvents((prev) => {
      const merged = [...prev];
      for (const e of newEvents) {
        if (!seenIds.current.has(e.id)) {
          seenIds.current.add(e.id);
          merged.push(e);
        }
      }
      return merged.sort((a, b) => a.created_at.localeCompare(b.created_at));
    });
  }

  useEffect(() => {
    setEvents([]);
    seenIds.current = new Set();
    setConnected(false);

    api
      .getScanEvents(scanId)
      .then(addEvents)
      .catch(() => {});

    const ws = new WebSocket(`${wsBase()}/ws/scans/${scanId}`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (msg) => {
      try {
        const e = JSON.parse(msg.data) as ScanEvent;
        addEvents([e]);
      } catch {
        // ignore malformed message
      }
    };

    return () => ws.close();
  }, [scanId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`inline-block w-1.5 h-1.5 rounded-full ${
            connected ? "bg-success" : "bg-foreground-muted"
          }`}
        />
        <span className="text-[11px] text-foreground-muted font-mono">
          {connected ? "live" : "reconnecting..."}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto space-y-1 font-mono text-[12px] max-h-80">
        {events.length === 0 && (
          <div className="text-foreground-muted">No events yet.</div>
        )}
        {events.map((e) => (
          <div key={e.id} className="flex gap-2">
            <span className="text-foreground-muted shrink-0">
              {new Date(e.created_at).toLocaleTimeString()}
            </span>
            <span className="text-accent">{e.event_type}</span>
            {Object.keys(e.payload).length > 0 && (
              <span className="text-foreground-muted truncate">
                {JSON.stringify(e.payload)}
              </span>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
