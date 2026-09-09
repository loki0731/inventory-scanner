import { InventoryHistoryEvent } from '../../types';
import { fmt } from '../../utils/format';
import { Empty } from '../common/Empty';

export function Changes({ events }: { events: InventoryHistoryEvent[] }) {
  if (!events.length) return <Empty text="No inventory changes" />;
  return (
    <div className="change-list large">
      {events.map((x) => (
        <div key={x.id}>
          <span className={`event event-${x.event_type}`}>{x.event_type}</span>
          <div>
            <strong>{x.name}</strong>
            <span>{x.old_version || '—'} → {x.new_version || '—'} · {x.source || 'unknown'}</span>
          </div>
          <small>{fmt(x.occurred_at)}</small>
        </div>
      ))}
    </div>
  );
}