// Empty.tsx
export function Empty({ text }: { text: string }) {
  return (
    <div className="empty">
      <div>∅</div>
      <strong>{text}</strong>
    </div>
  );
}