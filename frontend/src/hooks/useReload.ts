import { useState, useCallback } from 'react';

/** Returns a counter + bump function. Add the counter to a useEffect dep array
 *  to force a refetch after a mutation (create/update/delete/scan/etc). */
export function useReload() {
  const [tick, setTick] = useState(0);
  const bump = useCallback(() => setTick((x) => x + 1), []);
  return [tick, bump] as const;
}